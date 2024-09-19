def calculate_total_deposit(amount):
    """
    Calculate the total amount the buyer needs to deposit to cover fees.

    :param amount: The amount that should be received by the seller.
    :return: The total deposit amount including all fees.
    """
    # Total fee percentage (Oxapay's 0.4% + Your 0.2%)
    total_fee_percentage = 0.006  # 0.6%

    # Calculate the total deposit required
    total_deposit = amount / (1 - total_fee_percentage)

    return round(total_deposit, 2)


# Example usage
seller_amount = 100  # The amount the seller should receive
total_deposit = calculate_total_deposit(seller_amount)
print(f"The buyer needs to deposit: {total_deposit} USDT")
