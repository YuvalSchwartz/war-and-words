import csv

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import savgol_filter
from scipy.stats import f_oneway, ttest_ind

from utils import load_pickle


def generate_dataset_csv():
    """
    Generate a CSV file containing Gutenberg book ids along with their metadata and publication years.
    """
    book_id_to_name = load_pickle('data_dictionaries/book_id_to_name.pkl')
    book_id_to_author = load_pickle('data_dictionaries/book_id_to_author.pkl')
    book_id_to_lccn = load_pickle('data_dictionaries/book_id_to_lccn.pkl')
    book_id_to_wikipedia_url = load_pickle('data_dictionaries/book_id_to_wikipedia_url.pkl')
    book_id_to_year = load_pickle('data_dictionaries/book_id_to_year.pkl')

    with open('gutenberg_publication_years.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)

        # Write the header
        writer.writerow(['gutenberg_id', 'title', 'author', 'lccn', 'wikipedia_url', 'publication_year'])

        # Write the data rows
        for id, year in book_id_to_year.items():
            if year is not None:
                name = book_id_to_name.get(id, '') or ''
                author = book_id_to_author.get(id, '') or ''
                lccn = book_id_to_lccn.get(id, '') or ''
                wikipedia_url = book_id_to_wikipedia_url.get(id, '') or ''

                writer.writerow([id, name, author, lccn, wikipedia_url, year])


def plot_year_distribution(book_id_to_year, bin_width=10):
    """
    Plot the distribution of book publications by year (aggregated by bin_width).

    Args:
        book_id_to_year (dict): Dictionary mapping Gutenberg book IDs to publication years.
        bin_width (int): Width of the bins for aggregating publication counts.
    """
    # Aggregate counts by bin_width (e.g., decades)
    year_to_count = {}
    for book_id, year in book_id_to_year.items():
        if year is not None:
            binned_year = (year // bin_width) * bin_width
            year_to_count[binned_year] = year_to_count.get(binned_year, 0) + 1

    # Sort the years
    sorted_years = sorted(year_to_count.keys())
    counts = [year_to_count[year] for year in sorted_years]

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.bar(sorted_years, counts, width=bin_width * 0.8, color='skyblue', edgecolor='black', zorder=3)
    # plt.title('Distribution of Book Publications by Year', fontsize=16)
    plt.xlabel('Publication Year', fontsize=17)
    plt.ylabel('Number of Books Published', fontsize=17)
    plt.xticks(sorted_years[::max(1, len(sorted_years) // 20)], rotation=45, fontsize=14)  # Space out x-axis labels
    plt.yticks(fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
    plt.tight_layout()
    plt.savefig('figures/year_distribution.png')
    plt.show()


def plot_polarity_distribution(book_id_to_year, book_id_to_polarity, smooth=False, window_size=21, polyorder=2):
    """
    Plot the distribution of book polarities by year (optionally smoothed with Savitzky-Golay filter).

    Args:
        book_id_to_year (dict): Dictionary mapping Gutenberg book IDs to publication years.
        book_id_to_polarity (dict): Dictionary mapping Gutenberg book IDs to polarity scores.
        smooth (bool): Whether to apply smoothing with Savitzky-Golay filter.
        window_size (int): Window size for smoothing.
        polyorder (int): Polynomial order for smoothing.
    """
    # Aggregate polarities by year
    year_to_polarities = {}
    for book_id, year in book_id_to_year.items():
        if year in year_to_polarities:
            year_to_polarities[year].append(book_id_to_polarity[book_id])
        else:
            year_to_polarities[year] = [book_id_to_polarity[book_id]]

    # Calculate average polarity for each year
    sorted_years = sorted(year_to_polarities.keys())
    average_polarities = [np.mean(year_to_polarities[year]) for year in sorted_years]

    # Apply smoothing if enabled
    if smooth:
        smoothed_polarities = savgol_filter(average_polarities, window_length=window_size, polyorder=polyorder)
    else:
        smoothed_polarities = average_polarities

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(sorted_years, smoothed_polarities, color='skyblue', linewidth=3, zorder=3)
    # plt.title(f'Polarity Distribution by Year (Smoothed with window_length={window_size})' if smooth else 'Polarity Distribution by Year', fontsize=16)
    plt.xlabel('Publication Year', fontsize=21)
    plt.ylabel('Average Polarity', fontsize=21)
    plt.xticks(sorted_years[::max(1, len(sorted_years) // 20)], rotation=45, fontsize=18)  # Space out x-axis labels
    plt.yticks(fontsize=18)
    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
    plt.tight_layout()
    plt.savefig('figures/polarity_distribution.png' if smooth is False else 'figures/polarity_distribution_smoothed.png')
    plt.show()


def plot_sentiment_distribution(polarity_lists, ylim=None):
    """
    Plot the distribution of sentiment scores by time period.

    Args:
        polarity_lists (dict): Dictionary mapping time periods to lists of polarity scores.
        ylim (tuple): Tuple specifying the y-axis limits (in order to generate a zoomed-in plot).
    """
    # Create the box plot
    fig, ax = plt.subplots(figsize=(8, 7))
    box = ax.boxplot(list(polarity_lists.values()), patch_artist=True, tick_labels=[f"{period}\n(n={len(values)})" for period, values in polarity_lists.items()])
    plt.xticks(fontsize=13.5)
    plt.yticks(fontsize=13.5)

    # Assign colors to each time period
    colors = {
        "Pre-War": "#AAD2EC",  # Calm and stable
        "War": "#F69C9E",      # Intensity and conflict
        "Post-War": "#97E3C2"  # Renewal and hope
    }
    box_colors = [colors[period] for period in polarity_lists]
    for patch, color in zip(box['boxes'], box_colors):
        patch.set_facecolor(color)

    # Customize median line
    for median in box['medians']:
        median.set_color('black')  # Set color to black
        median.set_linewidth(2)    # Set line thickness

    # Customize y-axis
    # ax.set_title("Sentiment by Time Period", fontsize=16)
    ax.set_ylabel("Weighted-Average Polarity", fontsize=14)
    ax.set_xlabel("Time Period", fontsize=14)

    if ylim:
        ax.yaxis.set_major_locator(plt.MultipleLocator(0.02))
        plt.ylim(ylim)
    else:
        ax.yaxis.set_major_locator(plt.MultipleLocator(0.05))

    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
    fig.savefig('figures/sentiment_distribution.png' if ylim is None else 'figures/sentiment_distribution_zoomed.png')
    plt.show()


def plot_sentiment_heatmap(book_id_to_year, book_id_to_polarity):
    # Aggregate sentiment polarity by decade
    decade_to_polarities = {}
    for book_id, year in book_id_to_year.items():
        if year is not None:
            decade = (year // 10) * 10  # Group by decades
            if decade in decade_to_polarities:
                decade_to_polarities[decade].append(book_id_to_polarity[book_id])
            else:
                decade_to_polarities[decade] = [book_id_to_polarity[book_id]]

    # Calculate average polarity for each decade
    sorted_decades = sorted(decade_to_polarities.keys())
    average_polarities = [np.mean(decade_to_polarities[decade]) for decade in sorted_decades]

    # Create heatmap data
    heatmap_data = np.array(average_polarities).reshape(1, -1)  # Single row for heatmap

    # Adjust extent to center x-ticks in the middle of each decade
    decade_width = 10  # Width of each decade
    adjusted_extent = [
        sorted_decades[0] - decade_width / 2,
        sorted_decades[-1] + decade_width / 2,
        0,
        1
    ]

    # Plot heatmap
    plt.figure(figsize=(12, 3))
    plt.imshow(heatmap_data, cmap='coolwarm', aspect='auto', extent=adjusted_extent)
    colorbar = plt.colorbar(label="Average\nSentiment\nPolarity", pad=0.03)
    colorbar.ax.yaxis.label.set_size(20)  # Set font size for the label
    colorbar.ax.yaxis.labelpad = 10  # Adjust the label's distance from the colorbar
    colorbar.ax.tick_params(labelsize=16)  # Set the font size of the tick labels
    plt.xticks(sorted_decades, rotation=90, fontsize=16)
    plt.yticks([])  # Remove y-axis ticks since it's a single row
    # plt.title("Sentiment Polarity by Decade", fontsize=14)
    plt.xlabel("Decade", fontsize=20)
    plt.tight_layout()
    plt.savefig('figures/sentiment_decade_heatmap.png')
    plt.show()


def main():
    """
    Main function for analyzing the sentiment of books published around World War I (including statistical tests).
    """
    book_id_to_year = {book_id: year for book_id, year in load_pickle('data_dictionaries/book_id_to_year.pkl').items() if year is not None and abs(year - 1914) <= 2025 - 1914}
    plot_year_distribution(book_id_to_year)
    book_id_to_polarity = load_pickle('data_dictionaries/book_id_to_polarity.pkl')

    # Plot polarity distribution
    plot_polarity_distribution(book_id_to_year, book_id_to_polarity)
    plot_polarity_distribution(book_id_to_year, book_id_to_polarity, smooth=True)

    # Plot sentiment heatmap
    plot_sentiment_heatmap(book_id_to_year, book_id_to_polarity)

    # Define time periods and their centers
    time_periods = {
        "Pre-War": (lambda year: year < 1914, 1913),
        "War": (lambda year: 1914 <= year <= 1918, 1916),
        "Post-War": (lambda year: year > 1918, 1919)
    }

    # Group polarities and calculate weighted averages
    grouped_polarities = {period: [] for period in time_periods}

    for book_id, year in book_id_to_year.items():
        polarity = book_id_to_polarity[book_id]
        for period, (condition, center_year) in time_periods.items():
            if condition(year):
                weight = 1 / (1 + abs(year - center_year))  # calculate weights based on proximity to the center year (inverse of distance)
                grouped_polarities[period].append((polarity, weight))

    # Check group sizes and variances
    for period, polarities_weights in grouped_polarities.items():
        polarities = [p for p, _ in polarities_weights]
        variance = np.var(polarities)
        print(f"{period}: {len(polarities)} books, variance: {variance}")

    # Calculate weighted averages for each period
    weighted_averages = {}
    for period, polarities_weights in grouped_polarities.items():
        total_weighted_polarity = sum(p * w for p, w in polarities_weights)
        total_weight = sum(w for _, w in polarities_weights)
        weighted_averages[period] = total_weighted_polarity / total_weight

    print(f"\nWeighted Averages by Period: {weighted_averages}")

    # Extract polarity lists for statistical testing
    polarity_lists = {
        period: [p for p, _ in polarities_weights]
        for period, polarities_weights in grouped_polarities.items()
    }

    # Perform ANOVA
    anova_result = f_oneway(*[pol for pol in polarity_lists.values() if pol])
    print("\nANOVA result:", anova_result)

    # Perform pairwise t-tests with multiple comparisons correction
    pre_war = polarity_lists["Pre-War"]
    war = polarity_lists["War"]
    post_war = polarity_lists["Post-War"]

    p_values = []

    t_test_pre_war_vs_war = ttest_ind(pre_war, war, equal_var=False)
    p_values.append(t_test_pre_war_vs_war.pvalue)

    t_test_war_vs_post_war = ttest_ind(war, post_war, equal_var=False)
    p_values.append(t_test_war_vs_post_war.pvalue)

    print("T-Test Pre-War vs War:", t_test_pre_war_vs_war)
    print("T-Test War vs Post-War:", t_test_war_vs_post_war)

    # Visualize sentiment distributions
    plot_sentiment_distribution(polarity_lists)
    plot_sentiment_distribution(polarity_lists, ylim=(-0.05, 0.23))


if __name__ == '__main__':
    # generate_dataset_csv()
    main()