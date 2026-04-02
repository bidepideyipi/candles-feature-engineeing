``` shell
mongosh "mongodb://127.0.0.1:27017/technical_analysis" --eval "db.normalizer.deleteMany({})"

mongosh "mongodb://127.0.0.1:27017/technical_analysis" --eval "db.features_prediction.deleteMany({})"

mongoimport --uri "mongodb://127.0.0.1:27017/technical_analysis" --collection normalizer --type csv --headerline --file normalizer.csv

mongoimport --uri "mongodb://127.0.0.1:27017/technical_analysis" --collection config --type csv --headerline --file config.csv

mongosh "mongodb://127.0.0.1:27017/technical_analysis" --eval "db.normalizer.find().limit(10).forEach(printjson)"

mongosh "mongodb://127.0.0.1:27017/technical_analysis" --eval "db.config.find().limit(10).forEach(printjson)"

mongosh "mongodb://127.0.0.1:27017/technical_analysis" --eval "db.features_prediction.find().limit(10).forEach(printjson)"

mongoexport --uri "mongodb://127.0.0.1:27017/technical_analysis" --collection features_prediction --type=csv --fields="_id,timestamp,inst_id,bar,close_1h_normalized,volume_1h_normalized,rsi_14_1h,macd_line_1h,macd_signal_1h,macd_histogram_1h,hour_cos,hour_sin,day_of_week,upper_shadow_ratio_1h,lower_shadow_ratio_1h,shadow_imbalance_1h,body_ratio_1h,rsi_14_15m,volume_impulse_15m,macd_line_15m,macd_signal_15m,macd_histogram_15m,atr_15m,stoch_k_15m,stoch_d_15m,rsi_14_4h,trend_continuation_4h,macd_line_4h,macd_signal_4h,macd_histogram_4h,atr_4h,adx_4h,plus_di_4h,minus_di_4h,ema_12_4h,ema_26_4h,ema_48_4h,ema_cross_4h_12_26,ema_cross_4h_26_48,upper_shadow_ratio_4h,lower_shadow_ratio_4h,shadow_imbalance_4h,body_ratio_4h,rsi_14_1d,atr_1d,bollinger_upper_1d,bollinger_lower_1d,bollinger_position_1d,upper_shadow_ratio_1d,lower_shadow_ratio_1d,shadow_imbalance_1d,body_ratio_1d,label_prediction,label_prediction_high,label_prediction_low,price" --out features_prediction.csv
```

查询1小时数据数量
```shell
db.candlesticks.countDocuments({ bar: '1H' })
```
删除features集合
```shell
db.features.deleteMany({})
```
确认features label 数量
```shell
db.features.countDocuments({
    $and: [
        { label: { $exists: true } },
        { label: { $ne: "" } },
        { label: { $ne: null } }
    ]
})
```