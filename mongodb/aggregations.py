"""Run two non-trivial MongoDB aggregation pipelines and print their results."""
from pymongo import MongoClient

db = MongoClient("mongodb://localhost:27017").ecommerce

# Revenue by product category. Line items are embedded in transactions, so
# unwind is local to each purchase document before joining the catalogue.
revenue_by_category = [
    {"$match": {"status": {"$in": ["completed", "shipped", "delivered"]}}},
    {"$unwind": "$items"},
    {"$lookup": {"from": "products", "localField": "items.product_id",
                  "foreignField": "product_id", "as": "product"}},
    {"$unwind": "$product"},
    {"$group": {"_id": "$product.category_id", "revenue": {"$sum": "$items.subtotal"},
                "units": {"$sum": "$items.quantity"}, "orders": {"$addToSet": "$transaction_id"}}},
    {"$project": {"_id": 0, "category_id": "$_id", "revenue": {"$round": ["$revenue", 2]},
                  "units": 1, "orders": {"$size": "$orders"}}},
    {"$sort": {"revenue": -1}}, {"$limit": 10},
]

# RFM-style segmentation: purchasing frequency, monetary value, and recency.
user_segmentation = [
    {"$match": {"status": {"$in": ["completed", "shipped", "delivered"]}}},
    {"$group": {"_id": "$user_id", "orders": {"$sum": 1}, "spend": {"$sum": "$total"},
                "last_purchase": {"$max": {"$dateFromString": {"dateString": "$timestamp"}}}}},
    {"$set": {"recency_days": {"$dateDiff": {"startDate": "$last_purchase", "endDate": "$$NOW", "unit": "day"}}}},
    {"$set": {"segment": {"$switch": {"branches": [
        {"case": {"$and": [{"$gte": ["$orders", 5]}, {"$gte": ["$spend", 1000]}, {"$lte": ["$recency_days", 30]}]}, "then": "high_value_active"},
        {"case": {"$and": [{"$gte": ["$orders", 2]}, {"$lte": ["$recency_days", 60]}]}, "then": "repeat_active"},
        {"case": {"$gt": ["$recency_days", 60]}, "then": "lapsed"}], "default": "occasional"}}}},
    {"$group": {"_id": "$segment", "users": {"$sum": 1}, "average_spend": {"$avg": "$spend"},
                "average_orders": {"$avg": "$orders"}, "average_recency_days": {"$avg": "$recency_days"}}},
    {"$project": {"_id": 0, "segment": "$_id", "users": 1,
                  "average_spend": {"$round": ["$average_spend", 2]},
                  "average_orders": {"$round": ["$average_orders", 2]},
                  "average_recency_days": {"$round": ["$average_recency_days", 1]}}},
    {"$sort": {"users": -1}},
]

for title, pipeline in (("Revenue by category", revenue_by_category), ("RFM segments", user_segmentation)):
    print("\n" + title)
    for row in db.transactions.aggregate(pipeline, allowDiskUse=True):
        print(row)
