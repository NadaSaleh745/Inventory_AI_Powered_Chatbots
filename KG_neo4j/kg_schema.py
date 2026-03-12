SCHEMA_PROMPT = """
Neo4j Knowledge Graph Schema:

NODES:
(:Customer {customerId, customerCode, customerName, email, phone, billingAddress1, billingCity, billingCountry, createdAt, updatedAt, isActive})
(:Vendor {vendorId, vendorCode, vendorName, email, phone, addressLine1, city, country, createdAt, updatedAt, isActive})
(:Site {siteId, siteCode, siteName, addressLine1, city, country, timeZone, createdAt, updatedAt, isActive})
(:Location {locationId, locationCode, locationName, createdAt, updatedAt, isActive})
(:Item {itemId, itemCode, itemName, category, unitOfMeasure, createdAt, updatedAt, isActive})
(:Asset {assetId, assetTag, assetName, serialNumber, category, status, cost, purchaseDate, createdAt, updatedAt})
(:Bill {billId, billNumber, billDate, dueDate, totalAmount, currency, status, createdAt, updatedAt})
(:PurchaseOrder {poId, poNumber, poDate, status, createdAt, updatedAt})
(:PurchaseOrderLine {poLineId, lineNumber, itemCode, description, quantity, unitPrice})
(:SalesOrder {soId, soNumber, soDate, status, createdAt, updatedAt})
(:SalesOrderLine {soLineId, lineNumber, itemCode, description, quantity, unitPrice})
(:AssetTransaction {assetTxnId, txnType, quantity, txnDate, note})

RELATIONSHIPS:
(:Location)-[:LOCATED_AT]->(:Site)
(:Location)-[:PARENT_LOCATION]->(:Location)
(:Asset)-[:LOCATED_AT_SITE]->(:Site)
(:Asset)-[:LOCATED_AT]->(:Location)
(:Asset)-[:SUPPLIED_BY]->(:Vendor)
(:Bill)-[:BILLED_BY]->(:Vendor)
(:PurchaseOrder)-[:ORDERED_FROM]->(:Vendor)
(:PurchaseOrder)-[:DELIVERS_TO]->(:Site)
(:PurchaseOrderLine)-[:LINE_OF]->(:PurchaseOrder)
(:PurchaseOrderLine)-[:ORDERS_ITEM]->(:Item)
(:SalesOrder)-[:ORDERED_BY]->(:Customer)
(:SalesOrder)-[:SHIPS_FROM]->(:Site)
(:SalesOrderLine)-[:LINE_OF]->(:SalesOrder)
(:SalesOrderLine)-[:SELLS_ITEM]->(:Item)
(:AssetTransaction)-[:TRANSACTION_FOR]->(:Asset)
(:AssetTransaction)-[:FROM_LOCATION]->(:Location)
(:AssetTransaction)-[:TO_LOCATION]->(:Location)
"""
