# --------------
#             __         __     __ 
#  ___  ___  / /_  ___  / /__  / /_
# / _ \/ _ \/ __/ / _ \/ / _ \/ __/
# \___/ .__/\__/ / .__/_/\___/\__/ 
#    /_/        /_/                
#


import numpy as np
import matplotlib.pyplot as plt



def _find_pnl_even_points(arr: np.ndarray) -> np.ndarray:
    """Finds the indices where the PnL crosses zero (breakeven points)."""
    # arr is like our pnl_values array
    signs = np.sign(arr)
    # Remove any zeros as it is not a sign change
    non_zero_indices = np.where(signs != 0)[0]
    if len(non_zero_indices) == 0:
        return np.array([])  # Return empty array if all are zero

    non_zero_arr = arr[non_zero_indices]
    signs = np.sign(non_zero_arr)  # recalculate the signs excluding zero values
    sign_changes = np.diff(signs)
    change_indices = non_zero_indices[np.where(sign_changes != 0)[0] + 1]  # adjust index to match the original array
    return change_indices

def plot_strategy(ostrat, days_forward: int = None, dte: int = None, partitions: int = None, savefig: str = None, show: bool = True):
    """Plots the P&L and expected P&L of the strategy
    Args:
        ostrat: An object representing the option strategy to be plotted.  
            It is expected to have methods like `add_pnl`, `expected_move`, `price_range`, `pnl_values`, 
            `expected_pnl_values`, `expected_profit`, `pop`, `days_to_expiration` and attributes `underlying_price`, 
            `title`, `underlying_symbol`, and `pnls`.
 
        days_forward (int, optional): The number of days to project the P&L forward. Used in `ostrat.add_pnl`. Defaults to None.
        dte (int, optional):  Days to expiration.  Used in `ostrat.add_pnl`. Defaults to None.
        partitions (int, optional): Number of partitions to calculate the P&L. Used in `ostrat.add_pnl`. Defaults to None.
        savefig (str, optional): The file path to save the plot to. If None, the plot is not saved. Defaults to None.
        show (bool, optional): Whether to display the plot. Defaults to True.  

    """

    # set up theo price curves if needed - this is noop if all None
    # common alternative would be to add these outside of plotting
    ostrat.add_pnl(days_forward=days_forward, dte=dte, partitions=partitions)

    underlying_price = ostrat.underlying_price
    title = ostrat.title
    underlying_symbol = ostrat.underlying_symbol

    stddev = ostrat.expected_move()
    price_range = ostrat.price_range()
    pnl_values = ostrat.pnl_values()
    expected_pnl_values = ostrat.expected_pnl_values()
    expected_profit = ostrat.expected_profit()
    pop = ostrat.pop()



    fig, ax1 = plt.subplots(figsize=(12, 7), facecolor="#f0f0f0")  # Light background
    ax1.set_facecolor("#ffffff") # white background for main plot

    # Setup 1-std bar = expected move lines with a softer look
    emmin = underlying_price - stddev
    emmax = underlying_price + stddev
    ax1.plot([emmin, emmax], [0, 0], color='#a8dadc', linestyle='-', linewidth=8, alpha=0.6, label=f"Expected Move ({emmin:.2f} - {emmax:.2f})") # Reduced thickness & muted color

    # Setup 2-std lines with a dash-dot pattern
    stdmin = underlying_price - 2 * stddev
    stdmax = underlying_price + 2 * stddev
    for std in [stdmin, stdmax]:
        ax1.axvline(std, color='#457b9d', linestyle='-.', alpha=0.7, label=f'2-std {std:.2f}')  # Darker, less obtrusive lines

    ax1.axvspan(underlying_price-2*stddev, underlying_price-stddev, color='0.95')
    ax1.axvspan(underlying_price-stddev, underlying_price+stddev, color='0.9')
    ax1.axvspan(underlying_price+stddev, underlying_price+2*stddev, color='0.95')
    ax1.axvline(underlying_price, color='darkgrey', linestyle='--')


    # Plot PnL with a vibrant blue and a slight shadow effect for depth
    ax1.plot(price_range, pnl_values, color='#2a6f97', linewidth=2.5, label=f"PnL Payoff: ExP({expected_profit:.2f}) POP({pop:.2f})", zorder=3)  # Darker shade of blue
    ax1.plot(price_range, pnl_values, color="#000000", linewidth=4, alpha=0.04, zorder=1)  # slight shadow to make the line "pop"
    # set up theo price curves

    if len(ostrat.pnls) > 1:
        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(ostrat.pnls[1:])))
        for idx, opnl in enumerate(ostrat.pnls[1:]):
            ax1.plot(
                price_range,
                opnl.calc_pnl_values(at_expire=True),
                label=f'PnL at {opnl.days_to_expiration} dte ExP({opnl.expected_profit:.2f}) POP({opnl.pop:.2f})',
                color=colors[idx],  # use a color map
                linewidth=1.3, linestyle='--', alpha=0.8, zorder=2)  # slightly softer lines

    ax1.set_xlabel('Underlying Price at Expiration', color='#343a40', fontsize=11)  # Darker font color
    ax1.set_ylabel('Profit / Loss', color='#2a6f97', fontsize=11)  # Corresponding color
    ax1.tick_params(axis='y', labelcolor='#2a6f97') # label ticks


    # Secondary y-axis for Expected P&L with a distinct color
    ax2 = ax1.twinx()
    ax2.plot(price_range, expected_pnl_values, color='#964f8e', linewidth=2, linestyle='-', label=f"Expected PnL", alpha=0.8)  # Lighter purple, solid line
    ax2.set_ylabel('Expected Profit / Loss', color='#964f8e', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='#964f8e')

    # Align y-axes to share the zero point for clarity
    max_y1 = max(abs(pnl_values.min()), abs(pnl_values.max()))
    max_y2 = max(abs(expected_pnl_values.min()), abs(expected_pnl_values.max()))
    ax1.set_ylim(-max_y1 * 1.1, max_y1 * 1.1)  # added padding
    ax2.set_ylim(-max_y2 * 1.1, max_y2 * 1.1)


    # Add breakeven (BE) points with subtle, dashed lines
    idxs = _find_pnl_even_points(pnl_values)
    for idx in idxs:
        price_point = price_range[idx]
        ax1.axvline(price_point, color='#e63946', linestyle=':', alpha=0.8, label=f'BE {price_point:.2f}')  # Red, dashed lines for BE

    ax1.axhline(0, color='#495057', linewidth=0.7)  # Zero line - lighter grey

    # Title with a more prominent appearance
    plt.title(f"{title}: {underlying_symbol} ({ostrat.days_to_expiration} DTE)", fontsize=13, fontweight='bold', color='#343a40')


    # Combine legends and adjust layout for better visibility
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)  #  legend position
    plt.tight_layout()  # make room for the axis titles
    ax1.grid(True, linestyle='--', alpha=0.5) # Grid overlay with alpha

    if savefig is not None:
        plt.savefig(savefig)
    if not show:
        plt.close()
    plt.show()
