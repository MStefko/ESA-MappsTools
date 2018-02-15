# coding=utf-8
""" Tools for analyzing power consumption over a flyby.

@author: Marcel Stefko
"""
from typing import Tuple

from datetime import datetime
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import iso8601
import re


class PowerConsumptionGraph:
    """Contains information about power consumption timeline during a specified flyby."""

    def __init__(self, name: str, CA_timestamp: str, sheet_path: str,
                 add_HAA: bool = True, power_limit_Wh: float = None) -> None:
        """ Creates a power consumption analysis graph from a MAPPS resources datapack.

        :param name: Name of analysis (or flyby)
        :param CA_timestamp: UTC timestamp of closest approach, e.g. '2031-04-25T22:40:47'
        :param sheet_path: Path to .csv MAPPS datapack
        :param add_HAA: whether to manually add HAA data (since MAPPS doesn't output it yet)
        :param power_limit_Wh: limit on total power consumed during flyby
        """
        self.name = name
        self.CA = iso8601.parse_date(CA_timestamp)
        self.time_step_s = self._parse_time_step_from_sheet(sheet_path)
        self.power_limit_Wh = power_limit_Wh

        # Read the MAPPS datapack, skipping the comment rows and the row with units
        df = pd.read_csv(sheet_path, skiprows=list(range(22)) + [23], index_col=0)
        # Remove all non-power columns from the dataframe
        column_names = df.columns[:]
        for column_name in column_names:
            if not column_name.startswith("Power"):
                df.drop(column_name, axis=1, inplace=True)
        # Reformat the timestamps in row indexes
        df.rename(self._transform_timestamp_to_hours_from_CA, inplace=True)
        # Strip the string "Power " from column names
        df.rename(columns=self._strip_power_from_column_label, inplace=True)
        # Rename the row index axis
        df = df.rename_axis("Time [h]")
        if add_HAA:
            self._add_HAA_to_dataframe(df)
        self.data = df

    def print_total_power_consumed(self) -> str:
        """ Prints the total consumed power during the flyby.
        """
        consumed = self.get_cumulative_power().values[-1]
        message = f"Total power consumed: {consumed:.1f}"
        if self.power_limit_Wh is not None:
            message += f" ({100*consumed/self.power_limit_Wh:.1f}% of limit)."
        print(message)
        return message

    def print_individual_instrument_consumption(self) -> str:
        """ Prints a list of individual instrument power consumptions, and the percentage
        of the total power consumption for each instrument.
        """
        total = self.get_cumulative_power().values[-1]
        message = "Consumption by instrument:\n"
        df = self._get_only_instrument_dataframe()
        for inst in df:
            consumed = df[inst].sum() / (3600.0 / self.time_step_s)
            message += f" - {inst: <5}: {consumed: 7.1f} Wh - {100*consumed/total:4.1f}%\n"
        print(message)
        return message

    def plot(self) -> plt.Figure:
        """ Generate stacked power consumption plot.
        Needs to be shown with plt.show() afterwards
        """
        X_LIMIT_H = [-15.0, 15.0]
        # Create pandas stacked plot and format the axis limits
        ax_left = plt.gca()

        ax_right: plt.Axes = ax_left.twinx()
        self._get_only_instrument_dataframe().plot.area(stacked=True, ax=ax_left)
        ax_left.set_xlim(X_LIMIT_H)
        # Plot the black power requirement line
        ax_left.plot(*self._get_power_profile(), label='LIMIT', c='k', lw=3)
        plt.ylabel('Power [W]')
        plt.title(f'{self.name} - power consumption')
        # Reverse the up-down order of labels in the legend because it looks better
        handles, labels = ax_left.get_legend_handles_labels()
        ax_left.grid()

        cumulative_power = self.get_cumulative_power()
        # Plot the cumulative power consumption on the right side
        ax_right.set_ylabel('Total consumed power [Wh]')
        ax_right.set_xlim(X_LIMIT_H)
        ax_right.plot(cumulative_power.index, cumulative_power,
                      label='CONSUMED', c='g', lw=3)
        ax_right.set_ylim(bottom=0.0)
        if self.power_limit_Wh is not None:
            ax_right.plot(X_LIMIT_H, [self.power_limit_Wh] * 2, label='LIMIT', c='r', lw=3)

        # hack to get the left legend displayed on top on a third axis
        ax_left.legend().set_visible(False)
        ax3 = ax_left.twinx()
        ax3.legend(handles[::-1], labels[::-1], loc='upper left')
        ax3.yaxis.set_major_locator(plt.NullLocator())

        ax_right.legend(loc='upper right')
        return plt.gcf()

    @staticmethod
    def _get_power_profile() -> Tuple[np.ndarray, np.ndarray]:
        """ Returns the black curve for plotting required power profile.
        :return: Curve profile
        """
        x = np.array([-12.0, -12.0, -8.0, -8.0, -0.25, -0.25,
                      0.25, 0.25, 8.0, 8.0, 12.0, 12.0])
        y = np.array([0.0, 80.0, 80.0, 230.0, 230.0, 360.0,
                      360.0, 230.0, 230.0, 80.0, 80.0, 0.0])
        return (x, y)

    def _get_only_instrument_dataframe(self) -> pd.DataFrame:
        """

        :return: Dataframe with only instrument power consumption entries
        """
        columns = ['JMAG', 'PEP', '3GM', 'RPWI', 'SWI',
                   'RIME', 'JANUS', 'MAJIS', 'GALA', 'UVS']
        if 'HAA' in self.data:
            columns = ['HAA'] + columns
        return self.data[columns]

    def get_cumulative_power(self) -> pd.Series:
        """ Calculate cumulative power consumption:
         - Sum all instruments
         - Do a cumulative sum along the time axis
         - Renormalize by time step to get values in Wh

        :return: Cumulative power consumption
        """
        df = self._get_only_instrument_dataframe()
        return df.sum(axis=1).cumsum() / (3600.0 / self.time_step_s)

    @staticmethod
    def _add_HAA_to_dataframe(df: pd.DataFrame):
        """ Adds entry for power consumption of High-Accuracy Accelerometer to the class,
        where the HAA is turned on between (-12h, 12h), and has consumption of 15W.

        :param df: Dataframe to add the entry to.
        """
        haa = pd.Series(data=np.zeros(len(df.index)), index=df.index)

        def get_HAA_power_value_for_time_from_CA(time_h: float) -> float:
            return 15.0 if abs(time_h) < 12 else 0.0

        for time in haa.index:
            haa[time] = get_HAA_power_value_for_time_from_CA(time)
        df['HAA'] = haa

    @staticmethod
    def _parse_time_step_from_sheet(sheet_path: str) -> float:
        """  Read 11-th line of datapack (which is the time step) and parse the floating number
        :param sheet_path: Path to MAPPS datapack
        :return: Time step value in seconds
        """
        with open(sheet_path) as f:
            for idx, line in enumerate(f):
                if idx == 10:
                    float_strings = re.findall("\d+\.\d+", line)
                    if len(float_strings) != 1:
                        raise ValueError("11-th line of sheet doesn't contain exactly 1 float.")
                    return float(float_strings[0])

    def _transform_timestamp_to_hours_from_CA(self, UTC_timestamp: str) -> float:
        """ Calculates delta time in hours from CA.

        :param UTC_timestamp: Timestamp of given index in UTC format
        :return: Delta time from CA to the given timestamp in hours.
        """
        T = iso8601.parse_date(UTC_timestamp)
        return (T - self.CA).total_seconds() / 3600.0

    @staticmethod
    def _strip_power_from_column_label(column_label: str) -> str:
        return column_label[6:]


class DataConsumptionGraph:
    """Contains information about data consumption timeline during a specified flyby."""

    def __init__(self, name: str, CA_timestamp: str, sheet_path: str,
                 add_HAA: bool = True, data_limit_Mbits: float = None) -> None:
        """ Creates a powerdata consumption analysis graph from a MAPPS resources datapack.

        :param name: Name of analysis (or flyby)
        :param CA_timestamp: UTC timestamp of closest approach, e.g. '2031-04-25T22:40:47'
        :param sheet_path: Path to .csv MAPPS datapack
        :param add_HAA: whether to manually add HAA data (since MAPPS doesn't output it yet)
        :param data_limit_Mbits: limit on total data acquired during flyby
        """
        self.name = name
        self.CA: datetime = iso8601.parse_date(CA_timestamp)
        self.time_step_s = self._parse_time_step_from_sheet(sheet_path)
        self.data_limit_Mbits = data_limit_Mbits

        # Read the MAPPS datapack, skipping the comment rows and the row with units
        df = pd.read_csv(sheet_path, skiprows=list(range(22)) + [23], index_col=0)
        # Remove all non-power columns from the dataframe
        column_names = df.columns[:]
        rates = [col for col in column_names if col.startswith("Data Rate")]
        accum = [col for col in column_names if col.startswith("Data Accumulated")]
        # Reformat the timestamps in row indexes
        df.rename(self._transform_timestamp_to_hours_from_CA, inplace=True)
        # Rename the row index axis
        df = df.rename_axis("Time [h]")

        self.data_rate = df[rates].copy()
        self.data_accum = df[accum].copy()
        # Strip the string "Data Rate " from column names
        self.data_rate.rename(columns=lambda s: self._lstrip_characters(s, 10), inplace=True)
        # Strip the string "Data Accumulated " from column names
        self.data_accum.rename(columns=lambda s: self._lstrip_characters(s, 17), inplace=True)

        if add_HAA:
            self._add_HAA()

    @staticmethod
    def _lstrip_characters(column_label: str, no_of_characters) -> str:
        return column_label[no_of_characters:]

    def print_total_data_acquired(self) -> str:
        """ Prints the total consumed power during the flyby.
        """
        consumed = self.get_cumulative_data().values[-1]
        message = f"Total data acquired: {consumed:.1f} Mbits"
        if self.data_limit_Mbits is not None:
            message += f" ({100*consumed/self.data_limit_Mbits:.1f}% of limit)."
        print(message)
        return message

    def print_individual_instrument_data(self) -> str:
        """ Prints a list of individual instrument data consumptions, and the percentage
        of the total data consumption for each instrument.
        """
        total = self.get_cumulative_data().values[-1]
        message = "Consumption by instrument:\n"
        df = self._get_only_instrument_dataframe(self.data_accum)
        for inst in df:
            acquired = df[inst].values[-1]
            message += f" - {inst: <5}: {acquired: 7.1f} Mbits - {100*acquired/total:4.1f}%\n"
        print(message)
        return message

    def plot(self) -> plt.Figure:
        """ Generate stacked power consumption plot.
        Needs to be shown with plt.show() afterwards
        """
        # Create pandas stacked plot and format the axis limits
        ax: plt.Axes = self._get_only_instrument_dataframe(self.data_accum).plot.area(stacked=True)
        ax.set_xlim([-10.0, 10.0])
        plt.ylabel('Total acquired data [Mbits]')
        plt.title(f'{self.name} - data acquired')
        # Reverse the up-down order of labels in the legend because it looks better
        handles, labels = ax.get_legend_handles_labels()

        ax.grid()

        cumulative_data = self.get_cumulative_data()
        ax.plot(cumulative_data.index, cumulative_data,
                label='MEMORY', c='k', lw=3)
        if self.data_limit_Mbits is not None:
            ax.plot([-10.0, 10.0], [self.data_limit_Mbits] * 2, label='LIMIT', c='r', lw=3)
            if ax.get_ylim()[1] < self.data_limit_Mbits:
                ax.set_ylim([0.0, 1.1*self.data_limit_Mbits])
        ax.legend(handles[::-1], labels[::-1], loc='upper left')
        return plt.gcf()

    @staticmethod
    def _get_only_instrument_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """

        :param df: Dataframe from which to extract instrument entries
        :return: Dataframe with only instrument entries
        """
        columns = ['JMAG', 'PEP', '3GM', 'RPWI', 'SWI',
                   'RIME', 'JANUS', 'MAJIS', 'GALA', 'UVS']
        if 'HAA' in df:
            columns = ['HAA'] + columns
        return df[columns]

    def get_cumulative_data(self) -> pd.Series:
        """ Get accumulated data total
        :return: Total accumulated data
        """
        return self.data_accum.sum(axis=1)

    def _add_HAA(self):
        """ Adds entry for power consumption of High-Accuracy Accelerometer to the class,
        where the HAA is turned on between (-12h, 12h), and has consumption of 15W.

        """
        haa = pd.Series(data=np.zeros(len(self.data_rate.index)), index=self.data_rate.index)

        def get_HAA_data_rate_for_time_from_CA(time_h: float) -> float:
            return 2.0 if abs(time_h) < 12 else 0.0

        for time in haa.index:
            haa[time] = get_HAA_data_rate_for_time_from_CA(time)
        self.data_rate['HAA'] = haa
        self.data_accum['HAA'] = haa.cumsum() * self.time_step_s / 1000.0

    @staticmethod
    def _parse_time_step_from_sheet(sheet_path: str) -> float:
        """  Read 11-th line of datapack (which is the time step) and parse the floating number
        :param sheet_path: Path to MAPPS datapack
        :return: Time step value in seconds
        """
        with open(sheet_path) as f:
            for idx, line in enumerate(f):
                if idx == 10:
                    float_strings = re.findall("\d+\.\d+", line)
                    if len(float_strings) != 1:
                        raise ValueError("11-th line of sheet doesn't contain exactly 1 float.")
                    return float(float_strings[0])

    def _transform_timestamp_to_hours_from_CA(self, UTC_timestamp: str) -> float:
        """ Calculates delta time in hours from CA.

        :param UTC_timestamp: Timestamp of given index in UTC format
        :return: Delta time from CA to the given timestamp in hours.
        """
        T = iso8601.parse_date(UTC_timestamp)
        return (T - self.CA).total_seconds() / 3600.0


if __name__ == '__main__':
    pcg = PowerConsumptionGraph("14C6", '2031-04-25T22:40:47',
                                r"tests\14c6_test_attitude_and_data.csv",
                                power_limit_Wh=4065.0)
    dcg = DataConsumptionGraph("14C6", '2031-04-25T22:40:47',
                               r"tests\14c6_test_attitude_and_data.csv",
                               data_limit_Mbits=30000.0)

    pcg.print_total_power_consumed()
    pcg.print_individual_instrument_consumption()

    dcg.print_total_data_acquired()
    dcg.print_individual_instrument_data()

    pcg.plot()
    plt.show()

    dcg.plot()
    plt.show()
