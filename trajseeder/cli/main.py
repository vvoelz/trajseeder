import typer

from . import setup
from . import calibrate
from . import run
from . import status
from . import clean
from . import retry_failed
from . import inspect
from . import verify

app = typer.Typer(
    help="trajseeder: seed molecular simulation systems from structure ensembles",
    #add_completion=False
    )


app.command()(setup.setup)
app.command()(calibrate.calibrate)
app.command()(run.run)
app.command()(status.status)
app.command()(clean.clean)
app.command()(retry_failed.retry_failed)
app.command()(inspect.inspect)
app.command()(verify.verify)



def main():
    app()


if __name__ == "__main__":
    main()
