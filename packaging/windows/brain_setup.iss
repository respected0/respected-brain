; Respected Brain - per-user Windows installer (no administrator rights); works without the Hub.
; Built by packaging/build_installer.py. The installer owns the program files in {app}; the product's own commands own
; everything else: `setup` (vault, settings, records), `repair`, `config`, `uninstall` (see docs/PRODUCT_CONTRACT.md).
; Shared with the Orchestrator installer: the install-path page, the Hub download, the maintenance page, /SET= and /PURGE=1.
#ifndef AppVersion
  #define AppVersion "0.1.0b2"
#endif
#ifndef StageDir
  #define StageDir "..\..\dist\RespectedBrain"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist"
#endif

[Setup]
AppId={{2F6A9C41-85D7-4B3E-9A10-C7E4D58B1F23}
AppName=Respected Brain
AppVersion={#AppVersion}
AppPublisher=Respected
AppCopyright=Copyright (c) 2026 RESPECTED (MIT)
DefaultDirName={localappdata}\Respected\RespectedBrain\app
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=RespectedBrain-Windows-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\respected-brain.exe
CloseApplications=yes
SetupLogging=yes
WizardStyle=modern

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[UninstallRun]
; the product removes its integrations and records (and with /PURGE=1 or a yes its settings and data); never the vault
Filename: "{app}\respected-brain.exe"; Parameters: "{code:UninstallArgs}"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveProduct"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
const
  ProductName = 'Brain';
  ProductExe = 'respected-brain.exe';
  ProductFolder = 'RespectedBrain';
  HubProductId = 'brain';
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{2F6A9C41-85D7-4B3E-9A10-C7E4D58B1F23}_is1';
  HubSetupName = 'RespectedHub-Windows-Setup.exe';
  HubReleasesPage = 'https://github.com/respected0/respected-hub/releases/latest';

var
  ChoicePage, MaintenancePage, IntegrationPage: TInputOptionWizardPage;
  IdentityPage: TInputQueryWizardPage;
  VaultPage: TInputDirWizardPage;
  DownloadPage: TDownloadWizardPage;
  Maintenance, SettingsMode, Leaving, PurgeData: Boolean;

{ ---- shared with the Orchestrator installer ---- }

// /NAME=value command-line switches (silent installs, the Hub, tests)
function CommandValue(Name: String; Default: String): String;
var
  I: Integer;
  Prefix: String;
begin
  Result := Default;
  Prefix := '/' + Name + '=';
  for I := 1 to ParamCount do
    if CompareText(Copy(ParamStr(I), 1, Length(Prefix)), Prefix) = 0 then
      Result := Copy(ParamStr(I), Length(Prefix) + 1, MaxInt);
end;

// one ` --set "key=value"` argument; quotes are dropped so a value cannot end its own argument
function SetArg(Assignment: String): String;
begin
  StringChangeEx(Assignment, '"', '', True);
  Result := ' --set "' + Assignment + '"';
end;

// every /SET=key=value switch, as the product's own --set arguments
function SwitchSettings(): String;
var
  I: Integer;
begin
  Result := '';
  for I := 1 to ParamCount do
    if CompareText(Copy(ParamStr(I), 1, 5), '/SET=') = 0 then
      Result := Result + SetArg(Copy(ParamStr(I), 6, MaxInt));
end;

// --set arguments as `config set` arguments
function ConfigArgs(SetArgs: String): String;
begin
  Result := SetArgs;
  StringChangeEx(Result, ' --set ', ' ', True);
end;

function ProgramExe(): String;
begin
  Result := ExpandConstant('{localappdata}\Respected\' + ProductFolder + '\app\' + ProductExe);
end;

function DataRoot(): String;
begin
  Result := ExpandConstant('{localappdata}\Respected\' + ProductFolder + '\data');
end;

// installed = the program and the product's own install record are both there; anything less is a fresh install
function IsInstalled(): Boolean;
begin
  Result := FileExists(ProgramExe()) and FileExists(DataRoot() + '\install-manifest.json');
end;

function HubExe(): String;
begin
  Result := ExpandConstant('{localappdata}\Respected\RespectedHub\app\respected-hub.exe');
end;

function HubDownloadUrl(): String;
begin
  Result := CommandValue('HUBURL', HubReleasesPage + '/download/' + HubSetupName);
end;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

function FetchHubSetup(): Boolean;
begin
  Result := False;
  try
    if WizardSilent then
      DownloadTemporaryFile(HubDownloadUrl(), HubSetupName, '', @OnDownloadProgress)
    else begin
      DownloadPage.Clear;
      DownloadPage.Add(HubDownloadUrl(), HubSetupName, '');
      DownloadPage.Show;
      try
        DownloadPage.Download;
      finally
        DownloadPage.Hide;
      end;
    end;
    Result := True;
  except
    Log('Hub indirilemedi: ' + GetExceptionMessage);
  end;
end;

// get the newest Hub when it is missing, install it, then open it on this product's install page
procedure ContinueWithHub;
var
  Code: Integer;
begin
  if not FileExists(HubExe()) then
    if FetchHubSetup() then
      Exec(ExpandConstant('{tmp}\' + HubSetupName), '/SILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_SHOWNORMAL, ewWaitUntilTerminated, Code);
  if FileExists(HubExe()) then
    Exec(HubExe(), '--install=' + HubProductId, '', SW_SHOWNORMAL, ewNoWait, Code)
  else if not WizardSilent then begin
    ShellExec('open', HubReleasesPage, '', '', SW_SHOWNORMAL, ewNoWait, Code);
    MsgBox('Respected Hub indirilip kurulamadı. Açılan sayfadan ' + HubSetupName + ' dosyasını indirip çalıştır; Hub, ' + ProductName + ' ürününü senin için kuracak.', mbInformation, MB_OK);
  end;
end;

// runs one of the product's own commands; Output gets its standard output lines
function RunProduct(Params: String; var Output: TExecOutput): Boolean;
var
  Code: Integer;
begin
  Result := ExecAndCaptureOutput(ProgramExe(), Params, '', SW_HIDE, ewWaitUntilTerminated, Code, Output) and (Code = 0);
  if not Result then Log(ProductExe + ' ' + Params + ' failed with exit code ' + IntToStr(Code));
end;

// the value of `config get <key>`, whose output is {"<key>": <value>} (one line or one member per line)
function CurrentSetting(Key: String): String;
var
  Output: TExecOutput;
  I, P: Integer;
begin
  Result := '';
  if not RunProduct('config get ' + Key, Output) then Exit;
  for I := 0 to GetArrayLength(Output.StdOut) - 1 do begin
    P := Pos('": ', Output.StdOut[I]);
    if P > 0 then begin
      Result := Trim(Copy(Output.StdOut[I], P + 3, MaxInt));
      if (Result <> '') and (Result[Length(Result)] = '}') then Result := Trim(Copy(Result, 1, Length(Result) - 1)); // one-line output
      if (Length(Result) >= 2) and (Result[1] = '"') then begin
        Result := Copy(Result, 2, Length(Result) - 2);
        StringChangeEx(Result, '\"', '"', True);
        StringChangeEx(Result, '\\', '\', True);
      end;
    end;
  end;
end;

// the AI tools keep our MCP server and hooks running from the program folder, and Restart Manager cannot close them:
// stop exactly the processes of this product's program (matched by full path), so an update or removal while they are open works
procedure StopRunningProduct;
var
  Code: Integer;
  AppDir: String;
begin
  AppDir := ExpandConstant('{app}');
  StringChangeEx(AppDir, '''', '''''', True);
  Exec(ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    '-NoProfile -NonInteractive -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq ''' + ProductExe +
    ''' -and $_.ExecutablePath -like ''' + AppDir + '\*'' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"',
    '', SW_HIDE, ewWaitUntilTerminated, Code);
  Sleep(700);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  StopRunningProduct;
end;

// unattended through the Hub: `Setup.exe /VERYSILENT /HUB=1`
function InitializeSetup(): Boolean;
begin
  Result := True;
  if WizardSilent and (CommandValue('HUB', '') <> '') then begin
    ContinueWithHub;
    Result := False;
  end;
end;

function UninstallerPath(): String;
begin
  Result := '';
  if RegQueryStringValue(HKCU, UninstallKey, 'UninstallString', Result) then Result := RemoveQuotes(Result);
end;

procedure CreateSharedPages;
begin
  ChoicePage := CreateInputOptionPage(wpWelcome, 'Kurulum yolu', 'Nasıl devam etmek istersin?',
    'İkisi de aynı ürünü kurar; fark, güncellemeleri ve ayarları nereden yöneteceğindir.', True, False);
  ChoicePage.Add('Respected Hub ile devam et (önerilen): kurulum, güncelleme ve ayarlar görsel arayüzden yönetilir');
  ChoicePage.Add('Yalnızca ' + ProductName + ': Hub olmadan; ayarlar bu kurucudan ya da komutlarla değiştirilir');
  ChoicePage.SelectedValueIndex := 0;
  MaintenancePage := CreateInputOptionPage(ChoicePage.ID, ProductName + ' kurulu', 'Ne yapmak istersin?',
    'Ayarların ve not kasan her seçenekte korunur.', True, False);
  MaintenancePage.Add('Onar / güncelle: programı bu kurucudaki sürümle (v{#AppVersion}) yenile');
  MaintenancePage.Add('Ayarları değiştir');
  MaintenancePage.Add('Kaldır');
  MaintenancePage.SelectedValueIndex := 0;
  DownloadPage := CreateDownloadPage('Hub indiriliyor', 'En güncel Respected Hub kurucusu indiriliyor...', @OnDownloadProgress);
end;

{ ---- Brain's own questions ---- }

function IntegrationKey(Index: Integer): String;
begin
  case Index of
    0: Result := 'integrations.global';
    1: Result := 'integrations.mcp';
    2: Result := 'integrations.schedule';
  else
    Result := 'integrations.shortcut';
  end;
end;

procedure InitializeWizard;
begin
  Maintenance := IsInstalled();
  CreateSharedPages;
  IdentityPage := CreateInputQueryPage(MaintenancePage.ID, 'Kimlik', 'Seni ve asistanını tanıyalım',
    'Üçü de isteğe bağlı; sonradan bu kurucudan, Hub''dan ya da "respected-brain config set" ile değiştirilebilir.');
  IdentityPage.Add('Adın:', False);
  IdentityPage.Add('Asistanının adı (ör. Jarvis):', False);
  IdentityPage.Add('Kısa tanıtım (ör. Yazılım geliştirici):', False);
  VaultPage := CreateInputDirPage(IdentityPage.ID, 'Not kasası', 'Notların nerede saklanacak?',
    'Boş veya yeni bir klasör seç. Mevcut notlarının üzerine yazılmaz ve kaldırırken kasan silinmez. Program kendisi sabit bir yere kurulur: ' + ExpandConstant('{localappdata}\Respected\RespectedBrain\app') + '.', False, '');
  VaultPage.Add('');
  VaultPage.Values[0] := CommandValue('VAULT', ExpandConstant('{userdocs}\RespectedOS'));
  IntegrationPage := CreateInputOptionPage(VaultPage.ID, 'Bağlantılar', 'Brain hangi araçlarla çalışsın?',
    'Hepsi isteğe bağlı; diğer AI aracı ayarların korunur ve her biri sonradan kapatılabilir.', False, False);
  IntegrationPage.Add('AI araçlarının oturumlarını hafızaya yakala (Claude, Codex, Gemini... hook ve kuralları)');
  IntegrationPage.Add('AI araçları hafızayı MCP sunucusu olarak kullanabilsin');
  IntegrationPage.Add('Sabah özeti zamanlanmış görevi (Windows Görev Zamanlayıcı)');
  IntegrationPage.Add('Masaüstüne not kasası kısayolu');
end;

// the answers of the identity and integrations pages as the product's own --set arguments
function PageSettings(): String;
var
  I: Integer;
begin
  Result := SetArg('user_name=' + IdentityPage.Values[0]) + SetArg('assistant_name=' + IdentityPage.Values[1]) +
            SetArg('user_bio=' + IdentityPage.Values[2]);
  for I := 0 to 3 do
    if IntegrationPage.Values[I] then Result := Result + SetArg(IntegrationKey(I) + '=true')
    else Result := Result + SetArg(IntegrationKey(I) + '=false');
end;

procedure LoadCurrentSettings;
var
  I: Integer;
begin
  IdentityPage.Values[0] := CurrentSetting('user_name');
  IdentityPage.Values[1] := CurrentSetting('assistant_name');
  IdentityPage.Values[2] := CurrentSetting('user_bio');
  for I := 0 to 3 do
    IntegrationPage.Values[I] := CurrentSetting(IntegrationKey(I)) = 'true';
end;

{ ---- page flow ---- }

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = ChoicePage.ID then Result := WizardSilent or Maintenance
  else if PageID = MaintenancePage.ID then Result := WizardSilent or not Maintenance
  else if (PageID = IdentityPage.ID) or (PageID = IntegrationPage.ID) then Result := Maintenance and not SettingsMode
  else if PageID = VaultPage.ID then Result := Maintenance;
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  if Leaving then Confirm := False;
end;

procedure Leave;
begin
  Leaving := True;
  WizardForm.Close;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Output: TExecOutput;
  Code: Integer;
begin
  Result := True;
  if WizardSilent then Exit;
  if (CurPageID = ChoicePage.ID) and (ChoicePage.SelectedValueIndex = 0) then begin
    ContinueWithHub;
    Result := False;
    Leave;
  end else if (CurPageID = MaintenancePage.ID) and (MaintenancePage.SelectedValueIndex = 1) then begin
    SettingsMode := True;
    LoadCurrentSettings;
  end else if (CurPageID = MaintenancePage.ID) and (MaintenancePage.SelectedValueIndex = 2) then begin
    Exec(UninstallerPath(), '', '', SW_SHOWNORMAL, ewNoWait, Code);
    Result := False;
    Leave;
  end else if (CurPageID = IntegrationPage.ID) and SettingsMode then begin
    // settings only: the product applies them (and its integrations) itself; the program files are not touched
    if RunProduct('config set' + ConfigArgs(PageSettings()), Output) then
      MsgBox('Ayarlar kaydedildi.', mbInformation, MB_OK)
    else
      MsgBox('Ayarlar kaydedilemedi; hiçbir şey değişmedi. Ayrıntı için: respected-brain config', mbError, MB_OK);
    Result := False;
    Leave;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Output: TExecOutput;
begin
  if CurStep <> ssPostInstall then Exit;
  // over an installed product the program files were just replaced: the product re-verifies them and its integrations
  if Maintenance then begin
    if not RunProduct('repair', Output) then
      RaiseException(ProductName + ' onarılamadı. Ürün kendi değişikliklerini geri aldı; kurucuyu yeniden çalıştırabilirsin.');
    if SwitchSettings() <> '' then
      if not RunProduct('config set' + ConfigArgs(SwitchSettings()), Output) then
        RaiseException(ProductName + ' onarıldı ama /SET ayarları uygulanamadı.');
    Exit;
  end;
  if not RunProduct('setup --vault "' + VaultPage.Values[0] + '"' + PageSettings() + SwitchSettings(), Output) then
    RaiseException(ProductName + ' kurulumu tamamlanamadı. Ürün kendi değişikliklerini geri aldı; kurucuyu yeniden çalıştırabilirsin.');
end;

{ ---- removal ---- }

// interactive removal asks about settings and data (the vault never goes); silent removal keeps them unless /PURGE=1
function InitializeUninstall(): Boolean;
begin
  Result := True;
  StopRunningProduct;
  PurgeData := CommandValue('PURGE', '') <> '';
  if not UninstallSilent then
    PurgeData := MsgBox('Ayarlar ve çalışma verileri de silinsin mi?' + #13#10 + '(Not kasan hiçbir durumda silinmez.)', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
end;

function UninstallArgs(Param: String): String;
begin
  if PurgeData then Result := 'uninstall --purge' else Result := 'uninstall';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep <> usPostUninstall then Exit;
  if PurgeData then DelTree(DataRoot(), True, True, True);
  RemoveDir(ExpandConstant('{localappdata}\Respected\' + ProductFolder));
  RemoveDir(ExpandConstant('{localappdata}\Respected'));
end;
