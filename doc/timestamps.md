# Processing timestamps

The timestamps package provides an easy way to convert between
absolute and relative timestamps in ITL files.

```python
>>> from spice_tools.timestamps import TimestampProcessor
# Create a processor, define closest approach time of 14C6
>>> p = TimestampProcessor('2031-04-25T22:40:47')
>>> p.utc2delta('2031-04-25T23:42:50')
'+01:02:03'
>>> p.delta2utc('+01:02:03')
'2031-04-25T23:42:50'
```

We can also use it to convert absolute timestamps in ITL files
into relative timestamps, to have a better idea about the timeline.

```python
>>> p.absolute_to_relative_timestamps_itl(
...     'tests\\test_itl_file_in.itl',
...     'tests\\test_itl_file_out.itl',
...     "CLS_APP_CAL")

# Now we compare the file with the reference file in the tests folder,
# to see if they match.
>>> import filecmp
>>> filecmp.cmp('tests\\test_itl_file_out.itl',
...             'tests\\test_itl_file_ref.itl',
...             shallow=False)
True
```