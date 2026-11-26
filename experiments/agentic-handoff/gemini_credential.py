"""Store a Gemini key locally and inject it into approved experiment processes."""
import argparse
import ctypes
from ctypes import wintypes
import getpass
import os
from pathlib import Path
import subprocess
import sys
import warnings

TARGET = "KPMG.Team1F.Gemini.DeveloperAPI"
KEY_NAME = "GOOGLE_API_KEY"
APPROVED = {"paired-simplified-v2": ("gemini_paired.py", "--run", "--simplified-v2"),
            "grounded-stage-a": ("gemini_paired.py", "--run", "--grounded-stage-a"),
            "scoped-stage-a": ("gemini_paired.py", "--run", "--scoped-stage-a"),
            "policy-stage-a": ("gemini_paired.py", "--run", "--policy-stage-a"),
            "policy-stage-b": ("gemini_paired.py", "--run", "--policy-stage-b"),
            "policy-stage-b-retry": ("gemini_paired.py", "--run", "--policy-stage-b-retry"),
            "schema-probe": ("gemini_schema_probe.py", "--run-once"),
            "simplified-schema-probe": ("gemini_schema_probe.py", "--run-once", "--simplified"),
            "continue-pairs": ("gemini_paired.py", "--run", "--continue-f03-f10")}
HERE = Path(__file__).resolve().parent
ALLOWED_ENV = {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA",
               "APPDATA", "SYSTEMDRIVE", "COMSPEC", "PATHEXT", "PYTHONUTF8"}
RUNNER_IMPORTS = "import typing_extensions, httpx, jsonschema, bs4, numpy, scipy, torch, sentence_transformers"


class CredentialError(RuntimeError):
    pass


class Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentials:
    def __init__(self):
        if sys.platform != "win32":
            raise CredentialError("The credential launcher requires Windows.")
        api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._read = api.CredReadW
        self._read.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.POINTER(ctypes.POINTER(Credential)))
        self._read.restype = wintypes.BOOL
        self._write = api.CredWriteW
        self._write.argtypes = (ctypes.POINTER(Credential), wintypes.DWORD)
        self._write.restype = wintypes.BOOL
        self._delete = api.CredDeleteW
        self._delete.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD)
        self._delete.restype = wintypes.BOOL
        self._free = api.CredFree
        self._free.argtypes = (ctypes.c_void_p,)
        self._free.restype = None

    def put(self, target, secret):
        blob = bytearray(secret.encode("utf-8"))
        if not 0 < len(blob) <= 2560:
            raise CredentialError("The key length is invalid.")
        array = (ctypes.c_ubyte * len(blob)).from_buffer(blob)
        item = Credential(Type=1, TargetName=target, CredentialBlobSize=len(blob),
                          CredentialBlob=array, Persist=2, UserName="Google AI Studio")
        try:
            if not self._write(ctypes.byref(item), 0):
                raise CredentialError(f"Credential Manager write failed (Windows {ctypes.get_last_error()}).")
        finally:
            ctypes.memset(array, 0, len(blob))

    def get(self, target):
        value = ctypes.POINTER(Credential)()
        if not self._read(target, 1, 0, ctypes.byref(value)):
            code = ctypes.get_last_error()
            if code == 1168:
                raise CredentialError("The Gemini credential is missing for this Windows session.")
            raise CredentialError(f"Credential Manager read failed (Windows {code}).")
        try:
            item = value.contents
            if not item.CredentialBlob or not 0 < item.CredentialBlobSize <= 2560:
                raise CredentialError("The saved credential has an invalid size.")
            try:
                return ctypes.string_at(item.CredentialBlob, item.CredentialBlobSize).decode("utf-8")
            except UnicodeDecodeError:
                raise CredentialError("The saved credential is not valid text.") from None
        finally:
            self._free(value)

    def delete(self, target):
        if not self._delete(target, 1, 0):
            raise CredentialError(f"Credential Manager delete failed (Windows {ctypes.get_last_error()}).")


def check_environment(file, *, probe=subprocess.run):
    """Before any key is read: the isolated child must be able to import the paired runner's dependencies."""
    if file != "gemini_paired.py":
        return
    result = probe([sys.executable, "-I", "-c", RUNNER_IMPORTS], cwd=HERE, capture_output=True, check=False,
                   env={k: v for k, v in os.environ.items() if k.upper() in ALLOWED_ENV})
    if result.returncode:
        raise CredentialError(f"{sys.executable} cannot import the runner's dependencies in isolated mode. "
                              "Launch with the Stage A environment (requirements-stage-a.lock.txt).")


def launch(experiment, store, *, run=subprocess.run, probe=subprocess.run):
    if experiment not in APPROVED:
        raise CredentialError("That experiment has no launcher entry.")
    file, *flags = APPROVED[experiment]
    check_environment(file, probe=probe)
    secret = store.get(TARGET)
    if not secret.strip() or any(ch in secret for ch in ("\r", "\n", "\x00")):
        raise CredentialError("The saved credential is invalid.")
    # Avoid inheriting other provider credentials and endpoint configuration.
    child_env = {k: v for k, v in os.environ.items() if k.upper() in ALLOWED_ENV}
    child_env[KEY_NAME] = secret
    try:
        return run([sys.executable, "-I", "-B", "-c",
                    "import runpy,sys; script=sys.argv.pop(1); "
                    "sys.path.insert(0,sys.argv.pop(1)); runpy.run_path(script,run_name='__main__')",
                    str(HERE / file), str(HERE), *flags],
                   env=child_env, cwd=HERE, check=False).returncode
    except OSError:
        raise CredentialError("Could not start the approved Python experiment.") from None
    finally:
        child_env.pop(KEY_NAME, None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("store", "status", *APPROVED))
    args = parser.parse_args()
    try:
        store = WindowsCredentials()
        if args.action == "store":
            secret = os.environ.get(KEY_NAME, "").strip()
            if not secret:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("error", getpass.GetPassWarning)
                        secret = getpass.getpass("Gemini API key (input hidden): ").strip()
                except (getpass.GetPassWarning, EOFError):
                    raise CredentialError("A terminal with hidden input is required.") from None
            if not secret or any(ch in secret for ch in ("\r", "\n", "\x00")):
                raise CredentialError("No valid key was provided.")
            store.put(TARGET, secret)
            if store.get(TARGET) != secret:
                raise CredentialError("Credential verification failed.")
            print("Gemini credential saved and read back locally.")
        elif args.action == "status":
            store.get(TARGET)
            print("Gemini credential available to this shell.")
        else:
            raise SystemExit(launch(args.action, store))
    except CredentialError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
