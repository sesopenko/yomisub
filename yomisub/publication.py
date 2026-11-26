"""Serialize and recover destination-local subtitle replacements on POSIX filesystems."""

from contextlib import contextmanager
import fcntl
from hashlib import sha256
import os
from pathlib import Path
import shutil

import srt as srt_format

from .bundle import BundleStore, validate_name


def sync_path(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def mark(directory, name):
    marker = directory / name
    marker.touch(exist_ok=False)
    sync_path(marker)
    sync_path(directory)


class Publication:
    def __init__(self, video, language):
        validate_name(video.stem, language)
        basename = f"{video.stem}.{language}"
        key = sha256(os.fsencode(basename)).hexdigest()[:32]
        self.parent = video.parent
        self.paths = tuple(self.parent / f"{basename}.{ext}" for ext in ("srt", "ass", "yomisub.zip"))
        self.lock = self.parent / f".yomisub-{key}.lock"
        self.journal = self.parent / f".yomisub-{key}.txn"
        self.retired = self.parent / f".yomisub-{key}.done"

    @contextmanager
    def locked(self):
        with self.lock.open("a+b") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.recover()
            yield

    def recover(self):
        if self.retired.exists():
            shutil.rmtree(self.retired)
        if not self.journal.exists():
            return
        if (self.journal / "ready").exists() and not (self.journal / "committed").exists():
            for i, path in enumerate(self.paths):
                backup = self.journal / f"old-{i}"
                if backup.exists():
                    restore = self.journal / "restore"
                    restore.unlink(missing_ok=True)
                    os.link(backup, restore)
                    os.replace(restore, path)
                else:
                    path.unlink(missing_ok=True)
            sync_path(self.parent)
        # Retire the entire journal before removing its markers or backups.
        os.replace(self.journal, self.retired)
        sync_path(self.parent)
        shutil.rmtree(self.retired)

    def stage(self, srt, ass, bundle):
        self.journal.mkdir(mode=0o700)
        sync_path(self.parent)
        new = tuple(self.journal / f"new-{i}" for i in range(3))
        new[0].write_bytes(srt)
        new[1].write_bytes(ass)
        shutil.copyfile(bundle, new[2])
        list(srt_format.parse(new[0].read_text(encoding="utf8")))
        if "[Events]" not in new[1].read_text(encoding="utf8").splitlines():
            raise ValueError("ASS output is missing its events section.")
        evidence = BundleStore().load(new[2])
        if self.paths[0].name != f"{evidence.stem}.{evidence.stream.language}.srt":
            raise ValueError("Evidence bundle belongs to another destination.")
        for i, path in enumerate(self.paths):
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise ValueError(f"Expected a regular subtitle file at {path}.")
            if path.exists():
                backup = self.journal / f"old-{i}"
                os.link(path, backup)
                sync_path(backup)
            sync_path(new[i])
        mark(self.journal, "ready")
        return new


class FilePublisher:
    def publish(self, video: Path, language, srt, ass, bundle):
        transaction = Publication(video, language)
        with transaction.locked():
            try:
                new = transaction.stage(srt, ass, bundle)
                for staged, destination in zip(new, transaction.paths):
                    os.replace(staged, destination)
                sync_path(transaction.parent)
                mark(transaction.journal, "committed")
            finally:
                transaction.recover()
        return transaction.paths
