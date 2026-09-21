import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class ProjectManager:
    """Gerencia projetos locais em SQLite, sem depender de serviços externos."""

    def __init__(self, database_path=None):
        self.database_path = Path(database_path or Path.home() / ".ebookbuilder" / "projects.db")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    settings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    path TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    UNIQUE(project_id, path)
                );
                CREATE TABLE IF NOT EXISTS project_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    settings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_project(self, name, settings, project_id=None):
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(settings, ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            if project_id is None:
                cursor = connection.execute(
                    "INSERT INTO projects(name, settings_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (name, payload, now, now),
                )
                project_id = cursor.lastrowid
            else:
                connection.execute(
                    "UPDATE projects SET name=?, settings_json=?, updated_at=? WHERE id=?",
                    (name, payload, now, project_id),
                )
            connection.execute(
                "INSERT INTO project_versions(project_id, settings_json, created_at) VALUES (?, ?, ?)",
                (project_id, payload, now),
            )
        return project_id

    def get_project(self, project_id):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, name, settings_json, created_at, updated_at FROM projects WHERE id=?",
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "settings": json.loads(row[2]),
            "created_at": row[3],
            "updated_at": row[4],
        }

    def list_projects(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name, updated_at FROM projects ORDER BY updated_at DESC"
            ).fetchall()
        return [{"id": row[0], "name": row[1], "updated_at": row[2]} for row in rows]

    def list_assets(self, project_id):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, path, kind FROM project_assets "
                "WHERE project_id=? ORDER BY id",
                (project_id,),
            ).fetchall()
        return [{"id": row[0], "path": row[1], "kind": row[2]} for row in rows]

    def add_asset(self, project_id, path, kind="image"):
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO project_assets(project_id, path, kind) VALUES (?, ?, ?)",
                (project_id, str(path), kind),
            )

    def export_project(self, project_id, destination):
        project = self.get_project(project_id)
        if project is None:
            raise ValueError(f"Projeto inexistente: {project_id}")
        Path(destination).write_text(
            json.dumps(project, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
