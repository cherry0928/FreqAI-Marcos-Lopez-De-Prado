# Helper functions for trading indicators

import logging

import numpy as np
import pandas as pd
import talib.abstract as ta
from technical import qtpylib


logger = logging.getLogger(__name__)


def cusum_filter(df: pd.DataFrame, threshold_coeff: float) -> pd.DataFrame:
    """Sampling method using CUSUM given a threshold
        --------
        df: DataFrame must include 'colse' column
        threshold_coeff: percentage of daily volatility that defines sampling threshold"""

    # Daily volatility: 5mins x 288 = 1day
    df = daily_volatility(df, shift=288, lookback=50)

    df['entry_trigger'] = False
    df['cusum_pos_threshold'] = df['daily_volatility'] * threshold_coeff
    df['cusum_neg_threshold'] = df['daily_volatility'] * threshold_coeff * -1
    df['cusum_s_neg'] = 0

    s_pos = 0.0
    s_neg = 0.0

    # log returns
    diff = np.log(df['close']).diff()

    for i in diff.index:
        pos = float(s_pos + diff.loc[i])
        neg = float(s_neg + diff.loc[i])
        s_pos = max(0.0, pos)
        s_neg = min(0.0, neg)

        # Track cusum variables for plotting
        df.loc[i, 'cusum_s_pos'] = s_pos
        df.loc[i, 'cusum_s_neg'] = s_neg

        if s_neg < df.loc[i, 'cusum_neg_threshold']:
            s_neg = 0
            df.loc[i, 'entry_trigger'] = True

        elif s_pos > df.loc[i, 'cusum_pos_threshold']:
            s_pos = 0
            df.loc[i, 'entry_trigger'] = True

    return df


def daily_volatility(close: pd.DataFrame, shift: int, lookback: int):
    """Compute daily volatility of price series
        --------
        dataframe: must contain column for close
        shift: number of candles to shift one day
        lookback: period over which ema averaging will be computed over
        """

    log_returns_daily = np.log(close / close.shift(shift))
    daily_volatility = log_returns_daily.ewm(span=lookback).std(ddof=0)

    return daily_volatility


def top_percent_change(dataframe: pd.DataFrame, length: int) -> float:
    """
    Percentage change of the current close from the range maximum Open price
    :param dataframe: DataFrame The original OHLC dataframe
    :param length: int The length to look back
    """
    if length == 0:
        return (dataframe['open'] - dataframe['close']) / dataframe['close']
    else:
        return (dataframe['open'].rolling(length).max() - dataframe['close']) / dataframe['close']


def chaikin_mf(df, periods=20):
    close = df['close']
    low = df['low']
    high = df['high']
    volume = df['volume']
    mfv = ((close - low) - (high - close)) / (high - low)
    mfv = mfv.fillna(0.0)
    mfv *= volume
    cmf = mfv.rolling(periods).sum() / volume.rolling(periods).sum()
    return pd.Series(cmf, name='cmf')


# VWAP bands
def VWAPB(dataframe, window_size=20, num_of_std=1):
    df = dataframe.copy()
    df['vwap'] = qtpylib.rolling_vwap(df, window=window_size)
    rolling_std = df['vwap'].rolling(window=window_size).std()
    df['vwap_low'] = df['vwap'] - (rolling_std * num_of_std)
    df['vwap_high'] = df['vwap'] + (rolling_std * num_of_std)
    return df['vwap_low'], df['vwap'], df['vwap_high']


def EWO(dataframe, sma_length=5, sma2_length=35):
    df = dataframe.copy()
    sma1 = ta.EMA(df, timeperiod=sma_length)
    sma2 = ta.EMA(df, timeperiod=sma2_length)
    smadif = (sma1 - sma2) / df['close'] * 100
    return smadif


def get_distance(p1, p2):
    return abs((p1) - (p2))
