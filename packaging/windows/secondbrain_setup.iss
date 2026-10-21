; Respected SecondBrain - per-user Windows installer (no administrator rights); works without the Hub.
; Built by packaging/build_installer.py. The installer only carries the packaged distribution and the vault question:
; it unpacks the distribution to a temporary folder and runs the product's own `respectedbrain setup`, which writes the
; program folder, the data folder, the vault registration and the ownership records. Inno's {app} holds just the uninstaller.
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
AppName=Respected SecondBrain
AppVersion={#AppVersion}
AppPublisher=Respected
DefaultDirName={localappdata}\Respected\RespectedBrain\installer
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=RespectedSecondBrain-Windows-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
WizardStyle=modern

[Files]
Source: "{#StageDir}\*"; DestDir: "{tmp}\RespectedBrainStage"; Flags: ignoreversion recursesubdirs createallsubdirs deleteafterinstall

[Code]
var
  ChoicePage: TInputOptionWizardPage;
  HubChosen: Boolean;

function HubExe(): String;
begin
  Result := ExpandConstant('{localappdata}\Respected\RespectedHub\app\respected-hub.exe');
end;

function AlreadyInstalled(): Boolean;
begin
  Result := RegValueExists(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{2F6A9C41-85D7-4B3E-9A10-C7E4D58B1F23}_is1', 'UninstallString');
end;

// Two ways to the same installed product: through the Hub (recommended) or on its own. Silent installs and updates skip the question.
procedure CreateChoicePage;
begin
  ChoicePage := CreateInputOptionPage(wpWelcome, 'Kurulum yolu', 'Nasıl devam etmek istersin?',
    'İkisi de aynı ürünü kurar; fark, güncellemeleri ve ayarları nereden yöneteceğindir.', True, False);
  ChoicePage.Add('Respected Hub ile devam et (önerilen): kurulum, güncelleme ve ayarlar görsel arayüzden yönetilir');
  ChoicePage.Add('Yalnızca SecondBrain (gelişmiş / geliştiriciler için): Hub olmadan, bu kurucuyla');
  ChoicePage.SelectedValueIndex := 0;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = ChoicePage.ID) and (WizardSilent or AlreadyInstalled());
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  if HubChosen then Confirm := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Code: Integer;
begin
  Result := True;
  if WizardSilent or (CurPageID <> ChoicePage.ID) or (ChoicePage.SelectedValueIndex <> 0) then Exit;
  if FileExists(HubExe()) then
    Exec(HubExe(), '--install=secondbrain', '', SW_SHOWNORMAL, ewNoWait, Code)
  else begin
    ShellExec('open', 'https://github.com/respected0/respected-hub/releases/latest', '', '', SW_SHOWNORMAL, ewNoWait, Code);
    MsgBox('Respected Hub kurulu değil. Açılan sayfadan RespectedHub-Windows-Setup.exe dosyasını indirip çalıştırın; Hub, SecondBrain ürününü senin için kuracak.', mbInformation, MB_OK);
  end;
  HubChosen := True;
  Result := False;
  WizardForm.Close;
end;

var
  VaultPage: TInputDirWizardPage;

// /VAULT="C:\path" for silent installs
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

// the product's program folder; RESPECTED_APP_DIR is the product's own documented override
function ProgramRoot(Param: String): String;
begin
  Result := GetEnv('RESPECTED_APP_DIR');
  if Result = '' then
    Result := ExpandConstant('{localappdata}\Respected\RespectedBrain\app');
end;

procedure InitializeWizard;
begin
  CreateChoicePage;
  VaultPage := CreateInputDirPage(ChoicePage.ID, 'Not kasası', 'Notların nerede saklanacak?',
    'Boş veya yeni bir klasör seç. Mevcut notlarının üzerine yazılmaz ve kaldırırken kasan silinmez.', False, '');
  VaultPage.Add('');
  VaultPage.Values[0] := CommandValue('VAULT', ExpandConstant('{userdocs}\RespectedOS'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Stage: String;
  Code: Integer;
begin
  if CurStep <> ssPostInstall then Exit;
  Stage := ExpandConstant('{tmp}\RespectedBrainStage');
  // integrations (AI client hooks/MCP, schedule, shortcut) stay off, as in the Hub: they are chosen later
  if not Exec(Stage + '\respectedbrain.exe',
      'setup --vault "' + VaultPage.Values[0] + '" --package "' + Stage + '" --allow-unattested --no-global --no-mcp --no-schedule --no-shortcut',
      '', SW_HIDE, ewWaitUntilTerminated, Code) or (Code <> 0) then
    RaiseException('SecondBrain kurulumu tamamlanamadı (çıkış kodu ' + IntToStr(Code) + '). Kurucu yaptığı değişiklikleri geri aldı.');
end;

[UninstallRun]
; the product removes its own files and records; the vault and the data folder are kept
Filename: "{code:ProgramRoot}\respectedbrain.exe"; Parameters: "uninstall --keep-data --allow-unattested"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveProduct"
