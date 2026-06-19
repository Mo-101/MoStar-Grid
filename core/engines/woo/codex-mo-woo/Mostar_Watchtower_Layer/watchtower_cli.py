
import click
from intent_shadow import IntentShadowEngine
from moshock_integration import auto_monitor
from redeem_scroll import RedemptionEngine

@click.group()
def cli():
    pass

@cli.command()
@click.argument("identity")
def log(identity):
    text = input("🗣 Enter user text: ")
    IntentShadowEngine.log_interaction(identity, text)

@cli.command()
@click.argument("identity")
def monitor(identity):
    if auto_monitor(identity):
        print("🚨 Drift exceeded threshold.")
    else:
        print("✅ No significant drift detected.")

@cli.command()
@click.argument("identity")
def redeem(identity):
    scroll = input("📜 Enter redemption scroll: ")
    sigs = input("🔏 Enter 3 trust node signatures (comma-separated): ").split(",")
    RedemptionEngine.submit_redemption(identity, scroll, sigs)

if __name__ == "__main__":
    cli()
