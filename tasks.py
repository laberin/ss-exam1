from invoke import Collection, task

PYTHON = "python3"
VENV = ".ve"
CODE = "app"

ns = Collection()


@ns.add_task
@task()
def init(ctx):
    ctx.run(f"{PYTHON} -m venv .ve")
    ctx.run(f"{VENV}/bin/python -m pip install --upgrade pip")
    ctx.run(f"{VENV}/bin/python -m pip install poetry")
    ctx.run(f"{VENV}/bin/poetry config virtualenvs.create false")
    ctx.run(f"{VENV}/bin/poetry install")


@ns.add_task
@task()
def scheduler(ctx):
    """execute a scheduler"""
    ctx.run("PYTHONPATH=. celery -A app.scheduler worker -B -l INFO", pty=True)


@ns.add_task
@task()
def api(ctx):
    """execute an api server"""
    ctx.run(
        f"PYTHONPATH=. FLASK_ENV=production FLASK_APP=application PYTHONUNBUFFERED=TRUE {VENV}/bin/gunicorn app.api:app -w 2 --threads 2 -b 0.0.0.0:7070 --capture-output",
        pty=True,
    )
