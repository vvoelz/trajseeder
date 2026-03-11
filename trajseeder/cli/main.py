import typer

from . import calibrate
from . import plan
from . import run
from . import status

app = typer.Typer(help="trajseeder: seed molecular simulation systems from structure ensembles")


app.command()(calibrate.calibrate)
app.command()(plan.plan)
app.command()(run.run)
app.command()(status.status)


def main():
    app()


if __name__ == "__main__":
    main()
