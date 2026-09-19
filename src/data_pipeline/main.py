import typer

from .commands import (
    explanation_gen,
    spelling_check,
    synonym_gen,
    user_migration,
    word_consolidation,
    word_curation,
)

app = typer.Typer(rich_markup_mode=False)

app.command(name="consolidate-words")(word_consolidation.consolidate_words)
app.command(name="generate-explanations")(explanation_gen.generate_explanations)
app.command(name="migrate-user-data")(user_migration.migrate_user_data)
app.command(name="check-spelling")(spelling_check.check_spelling)
app.add_typer(word_curation.curate_app, name="curate-words")
app.add_typer(synonym_gen.app_synonym, name="generate-synonyms")


if __name__ == "__main__":
    app()
