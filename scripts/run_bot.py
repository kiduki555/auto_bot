import sys
import os
import click

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import main
import asyncio


@click.command()
@click.option('--mode', type=click.Choice(['live', 'paper']), default='paper',
              help='Trading mode: live or paper trading')
@click.option('--strategy', type=str, default='macd_crossover',
              help='Trading strategy to use')
@click.option('--symbol', type=str, default='BTCUSDT',
              help='Trading pair symbol')
@click.option('--interval', type=str, default='1h',
              help='Trading interval')
def run_bot(mode, strategy, symbol, interval):
    """Run the trading bot with specified parameters"""
    click.echo(f"Starting bot in {mode} mode...")
    click.echo(f"Strategy: {strategy}")
    click.echo(f"Symbol: {symbol}")
    click.echo(f"Interval: {interval}")
    
    # Set environment variables
    os.environ['TRADING_MODE'] = mode
    os.environ['STRATEGY'] = strategy
    os.environ['SYMBOL'] = symbol
    os.environ['INTERVAL'] = interval
    
    # Run the bot
    asyncio.run(main())


if __name__ == '__main__':
    run_bot()
