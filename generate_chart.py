import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_plot():
    # Connect to database
    conn = psycopg2.connect(
        dbname="jjm_triage",
        user="jjm_user",
        password="jjm_password",
        host="localhost",
        port="5432"
    )

    # Query data
    query = """
    SELECT 
        s.name as state,
        rs.band as severity_band,
        COUNT(ws.id) as count
    FROM water_samples ws
    JOIN risk_scores rs ON ws.id = rs.sample_id
    JOIN villages v ON ws.village_id = v.id
    JOIN districts d ON v.district_id = d.id
    JOIN states s ON d.state_id = s.id
    GROUP BY s.name, rs.band
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Define color palette for bands
    band_colors = {
        'Critical': '#d73027',
        'High': '#fc8d59',
        'Medium': '#fee08b',
        'Low': '#1a9850'
    }

    # Set style
    sns.set_theme(style="whitegrid", context="paper")
    plt.figure(figsize=(10, 6), dpi=300)

    # Create grouped barplot
    ax = sns.barplot(
        data=df, 
        x='state', 
        y='count', 
        hue='severity_band',
        palette=band_colors,
        hue_order=['Critical', 'High', 'Medium', 'Low']
    )

    plt.title('Water Quality Risk Band Distribution: Uttar Pradesh vs Bihar', fontsize=14, pad=15)
    plt.xlabel('State', fontsize=12)
    plt.ylabel('Number of Samples', fontsize=12)
    plt.legend(title='Severity Band', title_fontsize='11', fontsize='10')
    
    # Add exact numbers on top of bars
    for container in ax.containers:
        ax.bar_label(container, padding=3, fontsize=9)

    plt.tight_layout()
    plt.savefig('/home/anubhavanand/Documents/NTCC minor project/reports/assets/fig1_state_distribution.png')
    print("Plot saved to fig1_state_distribution.png")

if __name__ == "__main__":
    generate_plot()
