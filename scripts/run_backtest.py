import sys
import os
import click
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.backtest_config import BacktestConfig
from core.backtester import Backtester


@click.command()
@click.option('--strategy', type=str, default='macd_crossover',
              help='Strategy to backtest')
@click.option('--symbol', type=str, default='BTCUSDT',
              help='Trading pair symbol')
@click.option('--interval', type=str, default='1h',
              help='Trading interval')
@click.option('--start-date', type=str, default=None,
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=str, default=None,
              help='End date (YYYY-MM-DD)')
@click.option('--days', type=int, default=30,
              help='Number of days to backtest (if no dates specified)')
@click.option('--capital', type=float, default=10000,
              help='Initial capital')
@click.option('--risk-per-trade', type=float, default=1.0,
              help='Risk per trade (%)')
def run_backtest(strategy, symbol, interval, start_date, end_date,
                days, capital, risk_per_trade):
    """Run backtest with specified parameters"""
    
    # Set default dates if not provided
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (
            datetime.strptime(end_date, '%Y-%m-%d') -
            timedelta(days=days)
        ).strftime('%Y-%m-%d')
    
    click.echo("Starting backtest with parameters:")
    click.echo(f"Strategy: {strategy}")
    click.echo(f"Symbol: {symbol}")
    click.echo(f"Interval: {interval}")
    click.echo(f"Period: {start_date} to {end_date}")
    click.echo(f"Initial Capital: ${capital}")
    click.echo(f"Risk per Trade: {risk_per_trade}%")
    
    # Create backtest configuration
    config = BacktestConfig(
        strategy=strategy,
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital,
        risk_per_trade=risk_per_trade
    )
    
    # Run backtest
    backtester = Backtester(config)
    results = backtester.run()
    
    # Print results
    click.echo("\nBacktest Results:")
    click.echo(f"Total Returns: {results['total_returns']:.2f}%")
    click.echo(f"Win Rate: {results['win_rate']:.2f}%")
    click.echo(f"Profit Factor: {results['profit_factor']:.2f}")
    click.echo(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    click.echo(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    
    # Save results
    results_dir = os.path.join(
        os.path.dirname(__file__),
        '..',
        'backtest_results'
    )
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(
        results_dir,
        f"{strategy}_{symbol}_{interval}_{start_date}_{end_date}.html"
    )
    backtester.save_results(results_file)
    click.echo(f"\nDetailed results saved to: {results_file}")


if __name__ == '__main__':
    run_backtest()
