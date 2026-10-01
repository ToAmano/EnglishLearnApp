# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EnglishLearnApp is a bilingual English-Japanese dictionary and learning application with:
- **Streamlit frontend**: Main UI for word search, favorites, and study modes
- **React frontend** (in development): Located in `src/frontend_react/`
- **FastAPI backend**: REST API for the React frontend
- **SQLite databases**: Two separate databases for dictionary data and user data
- **Data pipeline**: CLI tools for managing word data, generating explanations, and data migrations

## Database Architecture

The application uses **two separate SQLite databases**:

### 1. Dictionary Database (`database/words.db`)
- **words**: Core vocabulary (word_id, word, source)
- **meanings**: Word definitions with parts of speech
- **examples**: Example sentences for each word
- **word_explanations**: AI-generated explanations in Japanese
- **stems**: Root words for derivation relationships
- **derived_words**: Maps words to their stems (many-to-many)
- **synonyms**: Bidirectional synonym relationships between word_ids
- **search_logs**: Tracks search frequency per word
- **vocab_status**: Learning status (unknown/passive/active) per word
- **favorites**: Favorited words (deprecated in dictionary DB, moved to user DB)

### 2. User Database (`database/user.db`)
- **favorites**: User's favorited words (word TEXT PRIMARY KEY)
- **vocab_status**: User's vocabulary learning status (word TEXT PRIMARY KEY, status TEXT)

**Critical**: The user database uses `word` (TEXT) as the primary key, while the dictionary database uses `word_id` (INTEGER). The backend layer handles conversion between these using `get_wordid_from_word()` and `get_word_from_wordid()` in `src/backend/core/db_core.py`.

Database connections are managed by:
- `get_db_connection()`: Returns connection to dictionary database
- `get_user_db_connection()`: Returns connection to user database

Environment variables `WORDS_DB_PATH` and `USER_DB_PATH` can override default database paths.

## Running the Application

### Streamlit App (Main UI)
```bash
streamlit run src/app.py
```

### FastAPI Backend
```bash
uvicorn src.api:app --reload
```

### React Frontend (Development)
```bash
cd src/frontend_react
npm run dev        # Start development server
npm run build      # Build for production
npm run lint       # Run ESLint
```

### Data Pipeline CLI
The `englishapp` command provides data management tools:

```bash
# Word consolidation and database operations
englishapp consolidate-words

# Generate AI explanations for words
englishapp generate-explanations

# Migrate user data from old schema to new
englishapp migrate-user-data

# Check spelling in word lists
englishapp check-spelling

# Word curation operations (has subcommands)
englishapp curate-words [subcommand]

# Generate synonyms (has subcommands)
englishapp generate-synonyms [subcommand]
```

## Code Architecture

### Backend Layer (`src/backend/`)
Business logic modules that abstract database operations:

- **backend.py**: Core search functions (meanings, examples, derived words, synonyms)
- **favorite.py**: Favorite management (`is_favorited`, `toggle_favorite`, `get_favorites_words`)
- **vocab_status.py**: Learning status management (`get_vocab_status`, `set_vocab_status`)
- **search_count.py**: Search frequency tracking
- **explanation.py**: Word explanations retrieval
- **learning.py**: Learning algorithms and word selection
- **core/db_core.py**: Database connection utilities and word/word_id conversion

### Frontend Layer (`src/frontend/`)
Streamlit UI components organized by tabs:

- **tab1_search.py**: Word search interface
- **tab4_favorite.py**: Favorites management
- **tab5_wordbatch.py**: Batch word review mode
- **tab6_wordcard.py**: Flashcard study mode
- **core.py**: Shared frontend utilities

### Database Initialization (`src/database/`)
Scripts to set up and populate databases:

- **step01_init_database_dictionary.py**: Create dictionary database schema
- **step01_init_database_user.py**: Create user database schema
- **step02_add_database_dictionary.py**: Populate dictionary with word data
- **step03_add_newwords_with_safeguard.py**: Safely add new words
- **make_example_database.py**: Populate example sentences

### Data Pipeline (`src/data_pipeline/`)
CLI tool built with Typer for data operations:

- **main.py**: CLI entry point with command registration
- **commands/**: Individual command implementations
  - **word_consolidation.py**: Merge and deduplicate word lists
  - **explanation_gen.py**: Generate AI explanations using LangChain
  - **user_migration.py**: Migrate between database schemas
  - **spelling_check.py**: Validate word spelling
  - **word_curation.py**: Manual word list curation
  - **synonym_gen.py**: Generate synonym relationships

## Code Quality Tools

This project uses pre-commit hooks for code quality. Install with:
```bash
pre-commit install
```

Pre-commit runs:
- **isort**: Import sorting (black profile)
- **black**: Code formatting (max line length: 150)
- **mypy**: Static type checking (strict mode, ignore missing imports)
- **flake8**: Linting with complexity checks
  - Max line length: 150
  - Max cyclomatic complexity: 10
  - Max expression complexity: 7
  - Max cognitive complexity: 7
- **pylint**: Additional linting (max line length: 150, ignores C0114/C0115/C0116)

**Important**: Pylint requires additional dependencies (pandas, streamlit, langchain, dotenv, langchain_google_genai) and has `sys.path.insert(0, 'src')` in its init-hook.

## Project Structure Notes

### Data Files (`src/data/`)
- **word_data/**: Source CSV files for different word levels and sources (eiken, lv2-lv12, buntan, etc.)
- **explanation_data/**: AI-generated explanations in Japanese
- **generate_examples/**: Example sentences generated for words
- **generate_synonym/**: Generated synonym relationships

### Synonym Graph Structure
Synonyms are stored as bidirectional edges in the `synonyms` table (word_id_1, word_id_2). The `find_synonym_ids()` function in `backend.py` performs breadth-first search to find all connected synonyms in the graph, not just direct neighbors.

### Derived Words
Words are connected to stem words via the `stems` and `derived_words` tables. A single word can have multiple stems, and multiple words can share the same stem (many-to-many relationship).

## Development Notes

- The application uses `.env` files for configuration (loaded via `python-dotenv`)
- LangChain with Google Generative AI is used for generating explanations
- The React frontend is a work in progress and coexists with the Streamlit app
- User authentication is not implemented; a default user ID is used
- Database paths default to `database/words.db` and `database/user.db` but can be overridden via environment variables
