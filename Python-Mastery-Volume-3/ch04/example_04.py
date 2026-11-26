stmt = select(OrderModel).options(joinedload(OrderModel.line_items))
