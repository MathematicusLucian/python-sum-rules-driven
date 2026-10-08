from datetime import datetime, date
import pandas as pd
import numpy as np
import pyspark.pandas as ps
from pyspark.sql import Row 
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

s = ps.Series([1, 3, 5, np.nan, 6, 8])
print(s)

psdf = ps.DataFrame(
    {'a': [1, 2, 3, 4, 5, 6],
     'b': [100, 200, 300, 400, 500, 600],
     'c': ["one", "two", "three", "four", "five", "six"]},
    index=[10, 20, 30, 40, 50, 60])

print(psdf)

dates = pd.date_range('20130101', periods=6)

print(dates)

pdf = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list('ABCD'))

print(pdf)

psdf = ps.from_pandas(pdf)
print(type(psdf))

sdf = spark.createDataFrame(pdf)
sdf.show()

df = spark.createDataFrame([
    Row(a=1, b=2., c='string1', d=date(2000, 1, 1), e=datetime(2000, 1, 1, 12, 0)),
    Row(a=2, b=3., c='string2', d=date(2000, 2, 1), e=datetime(2000, 1, 2, 12, 0)),
    Row(a=4, b=5., c='string3', d=date(2000, 3, 1), e=datetime(2000, 1, 3, 12, 0))
])
df.show()

print(df)

pandas_df = pd.DataFrame({
    'a': [1, 2, 3],
    'b': [2., 3., 4.],
    'c': ['string1', 'string2', 'string3'],
    'd': [date(2000, 1, 1), date(2000, 2, 1), date(2000, 3, 1)],
    'e': [datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 2, 12, 0), datetime(2000, 1, 3, 12, 0)]
})
df = spark.createDataFrame(pandas_df)
print(df)