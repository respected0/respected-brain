; Respected Brain - per-user Windows installer (no administrator rights); works without the Hub.
; Built by packaging/build_installer.py. The installer owns the program files in {app}; the product's own commands own
; everything else: `setup` (vault, settings, records), `repair`, `config`, `uninstall` (see docs/PRODUCT_CONTRACT.md).
; Shared with the Orchestrator installer: the install-path page, the Hub download, the maintenance page, /SET= and /PURGE=1.
#ifndef AppVersion
  #define AppVersion "0.1.0b1"
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
AppVerName=Respected Brain
UninstallDisplayName=Respected Brain
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
SetupIconFile=icon.ico
CloseApplications=yes
SetupLogging=yes
WizardStyle=modern
WizardImageFile=wizard\side-164x314.bmp,wizard\side-192x366.bmp,wizard\side-246x470.bmp,wizard\side-328x628.bmp
DisableWelcomePage=no
InfoAfterFile=UPDATE_NOTES.md
InfoBeforeFile=brain_info.txt

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Messages]
turkish.WizardInfoBefore=Bilgisayarında neler olur
turkish.InfoBeforeLabel=Kurulumda, kullanırken, güncellemede ve kaldırırken neler olacağını aşağıda okuyabilirsin.
turkish.WizardInfoAfter=Yenilikler
turkish.InfoAfterLabel=Bu sürümde neler değişti?
turkish.InfoAfterClickLabel=Devam etmek için Sonraki'ne tıklayın.
turkish.WelcomeLabel1=Respected Brain'e hoş geldin
turkish.WelcomeLabel2=Brain, AI araçlarının ortak hafızasını not kasanda tutar.%n%nYönetici izni gerekmez; mevcut notlarının üzerine yazılmaz.%n%nDevam etmek için Sonraki'ne tıkla.
turkish.FinishedHeadingLabel=Respected Brain hazır
; the ready page's button is "Kur", not "Sonraki"
turkish.ReadyLabel2a=Kuruluma devam etmek için Kur düğmesine, ayarları gözden geçirmek ya da değiştirmek için Önceki düğmesine tıklayın.
turkish.ReadyLabel2b=Kuruluma başlamak için Kur düğmesine tıklayın.

[Files]
Source: "{#StageDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[UninstallRun]
; the product removes its integrations and records (and with /PURGE=1 or a yes its settings and data); never the vault
Filename: "{app}\respected-brain.exe"; Parameters: "{code:UninstallArgs}"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveProduct"

[InstallDelete]
; an update replaces the program folder whole: files of the previous version (old dist-info, renamed modules) must not stay behind
Type: filesandordirs; Name: "{app}\app"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
#include "respected_cards.iss"

const
  ProductName = 'Brain';
  ProductExe = 'respected-brain.exe';
  ProductFolder = 'RespectedBrain';
  HubProductId = 'brain';
  InstallRecord = 'data\install-manifest.json';  // the product's own install record, relative to its folder
  UninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{2F6A9C41-85D7-4B3E-9A10-C7E4D58B1F23}_is1';
  HubSetupName = 'RespectedHub-Setup.exe';  // local file name only; the release asset carries a version
  HubReleasesPage = 'https://github.com/respected0/respected-hub/releases/latest';
  HubReleaseApi = 'https://api.github.com/repos/respected0/respected-hub/releases/latest';

var
  ChoicePage, MaintenancePage, IntegrationPage: TWizardPage;
  IdentityPage: TInputQueryWizardPage;
  ClientPage: TWizardPage;
  ClientList: TNewCheckListBox;
  ClientsReady: Boolean;
  ClientRow: array[0..10] of Integer;
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
  Result := FileExists(ProgramExe()) and FileExists(ExpandConstant('{localappdata}\Respected\' + ProductFolder + '\' + InstallRecord));
end;

function HubExe(): String;
begin
  Result := ExpandConstant('{localappdata}\Respected\RespectedHub\app\respected-hub.exe');
end;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

// the Hub installer is named after its version: take the Setup.exe asset of the newest Hub release
function HubDownloadUrl(): String;
var
  Json: AnsiString;
  Text: String;
  First, Last: Integer;
begin
  Result := CommandValue('HUBURL', '');
  if Result <> '' then Exit;
  DownloadTemporaryFile(HubReleaseApi, 'hub-latest.json', '', @OnDownloadProgress);
  LoadStringFromFile(ExpandConstant('{tmp}\hub-latest.json'), Json);
  Text := String(Json);
  Last := Pos('-Windows-x64-Setup.exe"', Text);
  if Last = 0 then RaiseException('Hub kurucusu sürüm listesinde yok');
  Last := Last + 21;
  First := Last;
  while (First > 1) and (Text[First - 1] <> '"') do First := First - 1;
  Result := Copy(Text, First, Last - First + 1);
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
    MsgBox('Respected Hub indirilip kurulamadı. Açılan sayfadan Hub kurucusunu (Setup.exe) indirip çalıştır; Hub, ' + ProductName + ' ürününü senin için kuracak.', mbInformation, MB_OK);
  end;
end;

// runs one of the product's own commands; Output gets its standard output lines
function RunProduct(Params: String; var Output: TExecOutput): Boolean;
var
  Code, I: Integer;
begin
  Result := ExecAndCaptureOutput(ProgramExe(), Params, '', SW_HIDE, ewWaitUntilTerminated, Code, Output) and (Code = 0);
  if not Result then begin
    Log(ProductExe + ' ' + Params + ' failed with exit code ' + IntToStr(Code));
    // the product explains the refusal on stdout (JSON conflicts) or stderr; without it the setup log names no cause
    for I := 0 to GetArrayLength(Output.StdOut) - 1 do Log('  stdout: ' + Output.StdOut[I]);
    for I := 0 to GetArrayLength(Output.StdErr) - 1 do Log('  stderr: ' + Output.StdErr[I]);
  end;
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
  ChoicePage := NewCardPage(0, wpWelcome, 'Kurulum yolu', 'İkisi de aynı ürünü kurar; fark, güncellemeleri ve ayarları nereden yöneteceğindir.', False);
  AddCard(ChoicePage, 0, #$E80F, 'Respected Hub ile devam et (önerilen)', 'Kurulum, güncelleme ve ayarlar görsel arayüzden yönetilir.', True);
  AddCard(ChoicePage, 0, #$E756, 'Yalnızca ' + ProductName, 'Hub olmadan; ayarlar bu kurucudan ya da komutlarla değiştirilir.', False);
  MaintenancePage := NewCardPage(1, ChoicePage.ID, ProductName + ' kurulu', 'Ayarların ve not kasan her seçenekte korunur.', False);
  AddCard(MaintenancePage, 1, #$E895, 'Onar / Güncelle', 'Programı bu kurucudaki sürümle (v{#AppVersion}) yeniler.', True);
  AddCard(MaintenancePage, 1, #$E713, 'Ayarları değiştir', 'Programa dokunmadan ayarları yeniden seçersin.', False);
  AddCard(MaintenancePage, 1, #$E74D, 'Kaldır', 'Programı kaldırır; sana sorarak ayarları ve verileri de siler.', False);
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

{ ---- which AI tools (the Hub's "Kaynaklar" and "İzinler" lists) ---- }

// rows 0..4: tools whose sessions are captured; rows 5..10: tools that may use the memory over MCP
function ClientId(K: Integer): String;
begin
  case K of
    0, 5: Result := 'claude';
    1: Result := 'codex';
    2: Result := 'gemini';
    3, 6: Result := 'antigravity';
    4, 7: Result := 'cursor';
    8: Result := 'windsurf';
    9: Result := 'claude-desktop';
  else
    Result := 'vscode-agents';
  end;
end;

function ClientName(Id: String): String;
begin
  if Id = 'claude' then Result := 'Claude Code'
  else if Id = 'codex' then Result := 'Codex'
  else if Id = 'gemini' then Result := 'Gemini CLI'
  else if Id = 'antigravity' then Result := 'Antigravity'
  else if Id = 'cursor' then Result := 'Cursor'
  else if Id = 'windsurf' then Result := 'Windsurf'
  else if Id = 'claude-desktop' then Result := 'Claude Desktop'
  else Result := 'Cline / Roo (VS Code)';
end;

// the same read-only check the product itself uses: has the tool a configuration folder on this computer
function ClientDetected(Id: String): Boolean;
var
  Home, Storage: String;
begin
  Home := ExpandConstant('{%USERPROFILE}');
  Storage := ExpandConstant('{userappdata}\Code\User\globalStorage\');
  if Id = 'claude' then Result := DirExists(Home + '\.claude') or FileExists(Home + '\.claude.json')
  else if Id = 'codex' then Result := DirExists(Home + '\.codex')
  else if (Id = 'gemini') or (Id = 'antigravity') then Result := DirExists(Home + '\.gemini')
  else if Id = 'cursor' then Result := DirExists(Home + '\.cursor')
  else if Id = 'windsurf' then Result := DirExists(Home + '\.codeium')
  else if Id = 'claude-desktop' then Result := DirExists(ExpandConstant('{userappdata}\Claude'))
  else Result := DirExists(Storage + 'saoudrizwan.claude-dev') or DirExists(Storage + 'rooveterinaryinc.roo-cline');
end;

function ClientsNeeded(): Boolean;
begin
  Result := CardChecked(2, 0) or CardChecked(2, 1);
end;

// the checked tools of rows First..Last as the product's comma list
function CollectClients(First, Last: Integer): String;
var
  K: Integer;
begin
  Result := '';
  for K := First to Last do
    if ClientList.Checked[ClientRow[K]] then begin
      if Result <> '' then Result := Result + ',';
      Result := Result + ClientId(K);
    end;
end;

// List empty = the product's default (every tool that is installed); otherwise exactly the listed tools
procedure SelectClients(First, Last: Integer; List: String);
var
  K: Integer;
begin
  for K := First to Last do
    if List = '' then ClientList.Checked[ClientRow[K]] := ClientDetected(ClientId(K))
    else ClientList.Checked[ClientRow[K]] := Pos(',' + ClientId(K) + ',', ',' + List + ',') > 0;
end;

// a group is only editable when its connection above is switched on
procedure EnableClientRows;
var
  K: Integer;
begin
  for K := 0 to 4 do ClientList.ItemEnabled[ClientRow[K]] := CardChecked(2, 0);
  for K := 5 to 10 do ClientList.ItemEnabled[ClientRow[K]] := CardChecked(2, 1);
end;

procedure ProductPageChanged(CurPageID: Integer);
begin
  if CurPageID <> ClientPage.ID then Exit;
  if not ClientsReady then begin
    SelectClients(0, 10, '');
    ClientsReady := True;
  end;
  EnableClientRows;
end;

// the last page of "change settings": the tool list when it is shown, otherwise the connections page
function LastSettingsPage(): Integer;
begin
  if ClientsNeeded() then Result := ClientPage.ID else Result := IntegrationPage.ID;
end;

procedure InitializeWizard;
var
  K: Integer;
begin
  TidyInfoPages;
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
  IntegrationPage := NewCardPage(2, VaultPage.ID, 'Bağlantılar', 'Brain hangi araçlarla çalışsın? Hepsi isteğe bağlı, sonradan kapatılabilir.', True);
  AddCard(IntegrationPage, 2, #$E8F1, 'Oturumları hafızaya yakala', 'Seçtiğin AI araçlarının oturumları hafızaya kaydedilir.', False);
  AddCard(IntegrationPage, 2, #$E8D4, 'Hafıza MCP sunucusu', 'Seçtiğin AI araçları notlarını arayıp okuyabilir.', False);
  AddCard(IntegrationPage, 2, #$E787, 'Sabah özeti görevi', 'Windows Görev Zamanlayıcı ile her sabah özet hazırlanır.', False);
  AddCard(IntegrationPage, 2, #$E8A7, 'Masaüstü kısayolu', 'Not kasasını açar; kasayı Obsidian''da en az bir kez açmış olmalısın.', False);
  ClientPage := CreateCustomPage(IntegrationPage.ID, 'AI araçları', 'Hangi araçlar? Bulunanlar işaretli gelir; sonradan Hub''dan değiştirebilirsin.');
  ClientList := TNewCheckListBox.Create(ClientPage);
  ClientList.Parent := ClientPage.Surface;
  ClientList.SetBounds(0, 0, ClientPage.SurfaceWidth, ClientPage.SurfaceHeight);
  ClientList.AddGroup('Oturumları hafızaya yakalanacak araçlar', '', 0, nil);
  for K := 0 to 4 do ClientRow[K] := ClientList.AddCheckBox(ClientName(ClientId(K)), '', 1, False, True, False, True, nil);
  ClientList.AddGroup('Hafızayı MCP ile kullanabilecek araçlar', '', 0, nil);
  for K := 5 to 10 do ClientRow[K] := ClientList.AddCheckBox(ClientName(ClientId(K)), '', 1, False, True, False, True, nil);
end;

// the answers of the identity and integrations pages as the product's own --set arguments
function PageSettings(): String;
var
  I: Integer;
begin
  Result := SetArg('user_name=' + IdentityPage.Values[0]) + SetArg('assistant_name=' + IdentityPage.Values[1]) +
            SetArg('user_bio=' + IdentityPage.Values[2]);
  for I := 0 to 3 do
    if CardChecked(2, I) then Result := Result + SetArg(IntegrationKey(I) + '=true')
    else Result := Result + SetArg(IntegrationKey(I) + '=false');
  if CardChecked(2, 0) then Result := Result + SetArg('integrations.clients=' + CollectClients(0, 4));
  if CardChecked(2, 1) then Result := Result + SetArg('integrations.mcp_clients=' + CollectClients(5, 10));
end;

procedure LoadCurrentSettings;
var
  I: Integer;
  Hooks, Mcp: String;
begin
  IdentityPage.Values[0] := CurrentSetting('user_name');
  IdentityPage.Values[1] := CurrentSetting('assistant_name');
  IdentityPage.Values[2] := CurrentSetting('user_bio');
  for I := 0 to 3 do
    SetCardChecked(2, I, CurrentSetting(IntegrationKey(I)) = 'true');
  Hooks := CurrentSetting('integrations.clients');
  Mcp := CurrentSetting('integrations.mcp_clients');
  if Mcp = '' then Mcp := Hooks;
  SelectClients(0, 4, Hooks);
  SelectClients(5, 10, Mcp);
  ClientsReady := True;
end;

{ ---- page flow ---- }

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = ChoicePage.ID then Result := WizardSilent or Maintenance
  else if PageID = MaintenancePage.ID then Result := WizardSilent or not Maintenance
  else if (PageID = IdentityPage.ID) or (PageID = IntegrationPage.ID) then Result := Maintenance and not SettingsMode
  else if PageID = VaultPage.ID then Result := Maintenance
  else if PageID = ClientPage.ID then Result := (Maintenance and not SettingsMode) or not ClientsNeeded()
  else if PageID = wpInfoAfter then Result := not Maintenance;
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
  // a connection that is on needs at least one tool
  if (CurPageID = ClientPage.ID) and ((CardChecked(2, 0) and (CollectClients(0, 4) = '')) or (CardChecked(2, 1) and (CollectClients(5, 10) = ''))) then begin
    MsgBox('Açık bıraktığın bağlantı için en az bir araç seç ya da önceki sayfada o bağlantının işaretini kaldır.', mbInformation, MB_OK);
    Result := False;
    Exit;
  end;
  if (CurPageID = ChoicePage.ID) and (CardSelectedIndex(0) = 0) then begin
    ContinueWithHub;
    Result := False;
    Leave;
  end else if (CurPageID = MaintenancePage.ID) and (CardSelectedIndex(1) = 1) then begin
    SettingsMode := True;
    LoadCurrentSettings;
  end else if (CurPageID = MaintenancePage.ID) and (CardSelectedIndex(1) = 2) then begin
    Exec(UninstallerPath(), '', '', SW_SHOWNORMAL, ewNoWait, Code);
    Result := False;
    Leave;
  end else if (CurPageID = LastSettingsPage()) and SettingsMode then begin
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
