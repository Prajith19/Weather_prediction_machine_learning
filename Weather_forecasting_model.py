import pandas as pd


weather = pd.read_csv("D:/weather.csv", index_col="DATE")
null_pct = weather.apply(pd.isnull).sum()/weather.shape[0]

valid_columns = weather.columns[null_pct < .05]

weather =  weather[valid_columns].copy()
weather.columns = weather.columns.str.lower()
print(weather)

weather = weather.ffill()
weather.apply(pd.isnull).sum()

weather.index = pd.to_datetime(weather.index)
print(weather.index)
print(weather.index.year)
print(weather.index.year.value_counts().sort_index())


weather["target"] = weather.shift(-1)["tmax"]
print(weather)

weather = weather.ffill()
print(weather)

from sklearn.linear_model import Ridge
rr = Ridge(alpha=.1)
predictors = weather.columns[~weather.columns.isin(["target", "name", "station"])]
print(predictors)

def backtest(weather, model, predictors, start=3650, step=90):
    all_predictions = []
    
    for i in range(start, weather.shape[0], step):
        train = weather.iloc[:i,:]
        test = weather.iloc[i:(i+step),:]
        
        model.fit(train[predictors], train["target"])
        
        preds = model.predict(test[predictors])
        preds = pd.Series(preds, index=test.index)
        
        combined = pd.concat([test["target"], preds], axis=1)
        
        combined.columns = ["actual", "prediction"]
        combined["diff"] = (combined["prediction"] - combined["actual"]).abs()
        
        all_predictions.append(combined)
    return pd.concat(all_predictions)

predictions = backtest(weather, rr, predictors)
print(predictions)

from sklearn.metrics import mean_absolute_error, mean_squared_error
mean_absolute_error(predictions["actual"], predictions["prediction"])

print(predictions["diff"].mean())

print(predictions.sort_values("diff", ascending=False))

print(pd.Series(rr.coef_, index=predictors))

def pct_diff(old, new):
    return (new - old) / old

def compute_rolling(weather, horizon, col):
    label = f"rolling_{horizon}_{col}"
    weather[label] = weather[col].rolling(horizon).mean()
    weather[f"{label}_pct"] = pct_diff(weather[label], weather[col])
    return weather
    
rolling_horizons = [3, 14]
for horizon in rolling_horizons:
    for col in ["tmax", "tmin", "prcp"]:
        weather = compute_rolling(weather, horizon, col)
        
weather = weather.iloc[14:,:]
weather = weather.fillna(0)

def expand_mean(df):
    return df.expanding(1).mean()

for col in ["tmax", "tmin", "prcp"]:
    weather[f"month_avg_{col}"] = weather[col].groupby(weather.index.month, group_keys=False).apply(expand_mean)
    weather[f"day_avg_{col}"] = weather[col].groupby(weather.index.day_of_year, group_keys=False).apply(expand_mean)

weather = weather.iloc[14:,:]
weather = weather.fillna(0)

predictors = weather.columns[~weather.columns.isin(["target", "name", "station"])]

predictions = backtest(weather, rr, predictors)
print(mean_absolute_error(predictions["actual"], predictions["prediction"]))

print(mean_squared_error(predictions["actual"], predictions["prediction"]))

print(predictions.sort_values("diff", ascending=False))

print(weather.loc["1990-03-07": "1990-03-17"])

change_graph = predictions["diff"].round().value_counts().sort_index() / predictions.shape[0]
 

print(predictions)