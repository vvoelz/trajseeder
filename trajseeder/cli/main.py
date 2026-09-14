import typer

from . import setup
from . import calibrate
from . import run
from . import status

app = typer.Typer(
    help="trajseeder: seed molecular simulation systems from structure ensembles",
    #add_completion=False
    )


app.command()(setup.setup)
app.command()(calibrate.calibrate)
app.command()(run.run)
app.command()(status.status)


def main():
    app()


if __name__ == "__main__":
    main()
