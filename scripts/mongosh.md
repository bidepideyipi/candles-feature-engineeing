``` shell
mongosh "mongodb://127.0.0.1:27017/technical_analysis" --eval "db.normalizer.deleteMany({})"

mongoimport \
    --uri="mongodb://127.0.0.1:27017" \
    --database="technical_analysis" \
    --collection="normalizer" \
    --type=csv \
    --headerline \
    --file="./scripts/normalizer.csv"
```