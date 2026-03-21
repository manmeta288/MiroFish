"""
Configuration management.
Loads the project-root .env for local dev. On Railway/Docker, platform env vars must win:
never use override=True, or a baked-in .env could replace NEO4J_PASSWORD / LLM keys and cause
Neo4j `Unauthorized` even when the Railway dashboard shows the correct values.
"""

import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

# override=False: process env (Railway, docker -e, shell) always takes precedence over .env
if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=False)
else:
    load_dotenv(override=False)


def _strip_env(key: str, default=None):
    v = os.environ.get(key, default)
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
    return v or None


def _resolve_neo4j() -> tuple[str, str, str | None, bool]:
    """
    Returns (uri, user, password, auth_disabled).

    Supports the same NEO4J_AUTH=username/password format as the official Neo4j Docker image,
    so MiroFish can reference the Neo4j service variable directly instead of duplicating
    NEO4J_PASSWORD (which often drifts). Password after first '/' (remainder is the password,
    so passwords may contain '/').
    """
    uri = _strip_env("NEO4J_URI") or "bolt://localhost:7687"
    if uri.lower().startswith("olt://"):  # common typo for bolt://
        uri = "bolt://" + uri[6:]
    user = _strip_env("NEO4J_USER") or "neo4j"
    password = _strip_env("NEO4J_PASSWORD")
    auth_line = _strip_env("NEO4J_AUTH")
    auth_disabled = False

    if auth_line is not None and auth_line.lower() == "none":
        auth_disabled = True
        password = None
    elif not password and auth_line:
        if "/" in auth_line:
            u, _, p = auth_line.partition("/")
            u = u.strip()
            p = p.strip()
            if u:
                user = u
            password = p if p else None

    return uri, user, password, auth_disabled


_NEO4J_URI, _NEO4J_USER, _NEO4J_PASSWORD, _NEO4J_AUTH_DISABLED = _resolve_neo4j()


class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # Return JSON with unicode characters un-escaped
    JSON_AS_ASCII = False

    # LLM (OpenAI-compatible)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')

    # Neo4j — see _resolve_neo4j(); set NEO4J_PASSWORD *or* NEO4J_AUTH=neo4j/secret (Docker style)
    NEO4J_URI = _NEO4J_URI
    NEO4J_USER = _NEO4J_USER
    NEO4J_PASSWORD = _NEO4J_PASSWORD
    NEO4J_AUTH_DISABLED = _NEO4J_AUTH_DISABLED

    # File uploads
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Text chunking
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # OASIS simulation
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def validate(cls):
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is not configured")
        if not cls.NEO4J_AUTH_DISABLED and not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD or NEO4J_AUTH (neo4j/password) is not configured")
        return errors

    @classmethod
    def neo4j_credentials_ready(cls) -> bool:
        return bool(cls.NEO4J_AUTH_DISABLED or cls.NEO4J_PASSWORD)
