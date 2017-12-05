# -*- coding: utf-8 -*-
""" Tools for manipulating timestamps in ITL and PTX files.

@author: Marcel Stefko
"""

import re
import os
from datetime import datetime, timedelta
import iso8601


class TimestampProcessor:
    """ Contains methods for manipulating relative and absolute UTC timestamps,
     and converting from one to another in ITL files."""

    def __init__(self, CA_timestamp_UTC: str):
        """ Construct the timestamp processor.

        :param CA_timestamp_UTC: Timestamp of closest approach time in UTC format
        (e.g. '2030-10-05T02:25:00'). From this timestamp the relative times will
        be calculated.
        """
        # Timestamp parsing regex
        self.RE = re.compile(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}[ Z]')
        self.CA = iso8601.parse_date(CA_timestamp_UTC)

    @staticmethod
    def _get_utc_date(initial_date: datetime, delta_seconds: float) -> str:
        """ Translate given datetime object by a given delta time.

        :param initial_date: Initial datetime.
        :param delta_seconds: Translation delta.
        :return: Translated datetime in UTC string isoformat.
        """
        final_date = initial_date + timedelta(seconds=delta_seconds)
        return final_date.isoformat()

    @staticmethod
    def _parse_delta_input(input_string: str) -> float:
        """

        :param input_string:
        :return:
        """
        if len(input_string) == 8:
            input_string = "+" + input_string
        t = datetime.strptime(input_string[1:], "%H:%M:%S")
        if input_string[0] == "+":
            delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        elif input_string[0] == "-":
            delta = - timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        else:
            raise ValueError("Incorrect input format, should be: '[+-]HH:MM:SS'.")
        return delta.total_seconds()

    def delta2utc(self, relative_timestamp: str) -> str:
        """ Transform relative timestamp to absolute timestamp.

        :param relative_timestamp: Timestamp in format '[+-]%HH:%MM:%SS.00000'
        :return: Absolute timestamp in format '%YYYY-%MM-%DDT%HH:%MM:%SS'
        """
        return str(self._get_utc_date(self.CA, self._parse_delta_input(relative_timestamp))[:-6])

    def utc2delta(self, utc_timestamp: str, enforce_24h: float = True) -> str:
        """ Transform an absolute UTC timestamp into a relative timestamp.

        :param enforce_24h: Flag to determine if timestamps more than 24 hours
        away from CA should be parsed. Output format not guaranteed.
        :param utc_timestamp: Absolute timestamp in UTC format.
        :return: Relative timestamp in format '[+-]HH:MM:DD' if under 24 hours.
        """
        T = iso8601.parse_date(utc_timestamp)
        # we will care about sign of relative timestamp later, now we want time amount
        delta = abs(self.CA - T)
        # If we have flag enabled, and time delta is outside 24 hour range, raise
        # an error.
        if enforce_24h:
            if delta.days != 0:
                raise ValueError("Timestamp is more than 24 hours away from CA and flag "
                                 "'enforce_24h' is set to True.")
        delta_timestamp = str(delta)
        # add a leading zero if timestamp is too short
        if len(delta_timestamp) == 7:
            delta_timestamp = "0" + delta_timestamp
        # add appropriate sign
        sign = "+" if T >= self.CA else "-"
        delta_timestamp = sign + delta_timestamp
        return delta_timestamp

    def absolute_to_relative_timestamps_itl(
            self, in_filepath: str, out_filepath: str,
            event_name: str, overwrite: bool = False) -> None:
        """ Take ITL file as input, and transform all absolute UTC timestamps into timestamps
        relative to event_name. The zero-time for relative timestamps is CA time given to the
        constructor of this class.

        - Original timestamps are moved to comments at the end of the given line.
        - Absolute timestamps in comments (after '#' sign) are ignored.
        - Lines with more than 1 absolute timestamp are ignored.

        :param in_filepath: Path to input ITL file
        :param out_filepath: Path to transformed output ITL file
        :param event_name: Name of event in EVT file (e.g. 'CLS_APP_CAL').
        :param overwrite: If False, an exception is raised in case out_filepath already exists.
        """
        if overwrite:
            if os.path.isfile(out_filepath):
                raise RuntimeError(f"File {out_filepath} already exists. If you want " +
                                   f"to overwrite it, set flag 'overwrite=True'.")
        with open(in_filepath) as f:
            lines = f.readlines()

        new_lines = []
        # First comment line of original timestamp
        new_lines.append(f'# {event_name} time used: {self.CA}\n')
        for idx, line in enumerate(lines):
            # strip all whitespace and linebreak characters from the right
            x = line[:]
            x = x.rstrip()
            # search for absolute timestamp
            if self.RE.findall(x):
                # if more than 1 timestamp on the line, skip it
                if len(self.RE.findall(x)) > 1:
                    print(f"Multiple timestamps found on line {idx}. Skipping...")
                    new_lines.append(x + '\n')
                    continue
                # Find the timestamp, and split rest of line to part before and after
                abs_timestamp = self.RE.findall(x)[0]
                sp = x.split(abs_timestamp)
                # If part before timestamp contains #, it means it is in a comment
                if "#" in sp[0]:
                    print(f"Timestamp on line {idx} is a comment. Skipping...")
                    new_lines.append(x + '\n')
                    continue

                # Properly format the relative timestamp
                rel_timestamp = self.utc2delta(abs_timestamp)
                # Join the two parts of split string together, with relative timestamp
                # inbetween, and the original absolute appended at the end in comment
                x = sp[0] + f" {event_name} {rel_timestamp} " + sp[1] + f" # {abs_timestamp} "
            new_lines.append(x + '\n')

            with open(os.path.abspath(out_filepath), 'w') as f:
                f.writelines(new_lines)


if __name__ == '__main__':
    p = TimestampProcessor('2031-04-25T22:40:47')
    p.absolute_to_relative_timestamps_itl('tests\\test_itl_file_out.itl', 'tests\\test_itl_file_out2.itl', "CAL")
