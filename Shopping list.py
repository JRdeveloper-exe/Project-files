foods = []
prices = []
total = 0
Store = input("Please enter Shop of choice: ")


while True:
    food = input("Please enter item (Press s to stop): ")
    if food.lower() == "s":
            break
    else:
        price = float(input(f"Please Enter the price of the item {food}: "))
        foods.append(food)
        prices.append(price)
print("-------YOUR CART-------")

for food in foods:
    print(f"{food}_ _ _ _                {price}")

for price in prices:
    total += price
    
print(f"Total nomination in carreer:     {total}")

