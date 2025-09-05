import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="NHL Fantasy Draft Tool",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    """Load the fantasy hockey data"""
    try:
        skaters = pd.read_csv('data/skaters_cat_league.csv')
        goalies = pd.read_csv('data/goalies_cat_league.csv')
        
        # Clean column names (remove quotes if present)
        skaters.columns = skaters.columns.str.replace('"', '')
        goalies.columns = goalies.columns.str.replace('"', '')
        
        # Convert numeric columns
        numeric_cols_skaters = ['VAR', 'GP', 'G', 'A', 'PTS', '(+/-)', 'PIM', 'EV', 
                               'PPG', 'PPA', 'PPP', 'SOG', 'ATOI', 'FOW', 'BLK', 'HIT']
        numeric_cols_goalies = ['VAR', 'GS', 'W', 'L', 'T/O', 'SO', 'SV', 'SV%', 
                               'GA', 'GAA', 'SA']
        
        for col in numeric_cols_skaters:
            if col in skaters.columns:
                skaters[col] = pd.to_numeric(skaters[col], errors='coerce')
        
        for col in numeric_cols_goalies:
            if col in goalies.columns:
                goalies[col] = pd.to_numeric(goalies[col], errors='coerce')
        
        # Fill NaN values with 0
        skaters = skaters.fillna(0)
        goalies = goalies.fillna(0)
        
        return skaters, goalies
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

def create_fantasy_scoring_inputs():
    """Create fantasy scoring input fields"""
    st.header("⚙️ Fantasy Scoring Settings")
    st.markdown("Customize your league's fantasy point values:")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("🏒 Skater Scoring")
        g_pts = st.number_input("Goals (G)", min_value=0.0, max_value=20.0, value=6.0, step=0.5, key="g_pts")
        a_pts = st.number_input("Assists (A)", min_value=0.0, max_value=20.0, value=4.0, step=0.5, key="a_pts")
        pim_pts = st.number_input("Penalty Minutes (PIM)", min_value=-5.0, max_value=5.0, value=1.0, step=0.1, key="pim_pts")
    
    with col2:
        st.subheader("⚡ Power Play")
        ppg_pts = st.number_input("PP Goals (PPG)", min_value=0.0, max_value=20.0, value=1.0, step=0.5, key="ppg_pts")
        ppp_pts = st.number_input("PP Points (PPP)", min_value=0.0, max_value=20.0, value=2.0, step=0.5, key="ppp_pts")
        
    with col3:
        st.subheader("💪 Physical")
        sog_pts = st.number_input("Shots on Goal (SOG)", min_value=0.0, max_value=5.0, value=0.25, step=0.05, key="sog_pts")
        hit_pts = st.number_input("Hits (HIT)", min_value=0.0, max_value=5.0, value=2.0, step=0.1, key="hit_pts")
        blk_pts = st.number_input("Blocks (BLK)", min_value=0.0, max_value=5.0, value=2.0, step=0.1, key="blk_pts")
    
    with col4:
        st.subheader("🥅 Goalie Scoring")
        w_pts = st.number_input("Wins (W)", min_value=0.0, max_value=20.0, value=2.0, step=0.5, key="w_pts")
        sv_pts = st.number_input("Saves (SV)", min_value=0.0, max_value=5.0, value=0.5, step=0.05, key="sv_pts")
        so_pts = st.number_input("Shutouts (SO)", min_value=0.0, max_value=20.0, value=2.0, step=0.5, key="so_pts")
    
    # Store scoring in a dictionary
    scoring = {
        'G': g_pts, 'A': a_pts, 'PIM': pim_pts, 'PPG': ppg_pts, 'PPP': ppp_pts,
        'SOG': sog_pts, 'HIT': hit_pts, 'BLK': blk_pts, 'W': w_pts, 'SV': sv_pts, 'SO': so_pts
    }
    
    return scoring

def calculate_fantasy_points(df, scoring, player_type='skater'):
    """Calculate fantasy points for each player"""
    df = df.copy()
    df['Fantasy Points'] = 0
    
    if player_type == 'skater':
        # Calculate skater fantasy points
        if 'G' in df.columns and 'G' in scoring:
            df['Fantasy Points'] += df['G'] * scoring['G']
        if 'A' in df.columns and 'A' in scoring:
            df['Fantasy Points'] += df['A'] * scoring['A']
        if 'PIM' in df.columns and 'PIM' in scoring:
            df['Fantasy Points'] += df['PIM'] * scoring['PIM']
        if 'PPG' in df.columns and 'PPG' in scoring:
            df['Fantasy Points'] += df['PPG'] * scoring['PPG']
        if 'PPP' in df.columns and 'PPP' in scoring:
            df['Fantasy Points'] += df['PPP'] * scoring['PPP']
        if 'SOG' in df.columns and 'SOG' in scoring:
            df['Fantasy Points'] += df['SOG'] * scoring['SOG']
        if 'HIT' in df.columns and 'HIT' in scoring:
            df['Fantasy Points'] += df['HIT'] * scoring['HIT']
        if 'BLK' in df.columns and 'BLK' in scoring:
            df['Fantasy Points'] += df['BLK'] * scoring['BLK']
    else:
        # Calculate goalie fantasy points
        if 'W' in df.columns and 'W' in scoring:
            df['Fantasy Points'] += df['W'] * scoring['W']
        if 'SV' in df.columns and 'SV' in scoring:
            df['Fantasy Points'] += df['SV'] * scoring['SV']
        if 'SO' in df.columns and 'SO' in scoring:
            df['Fantasy Points'] += df['SO'] * scoring['SO']
    
    df['Fantasy Points'] = df['Fantasy Points'].round(1)
    return df

def create_combined_rankings(skaters, goalies):
    """Create a combined ranking of all players"""
    # Select ALL relevant columns for skaters including the requested fantasy stats
    skater_cols = ['Player', 'Team', 'Pos', 'Fantasy Points', 'G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK']
    skaters_display = skaters[skater_cols].copy()
    skaters_display['Player Type'] = 'Skater'
    
    # Select relevant columns for goalies  
    goalie_cols = ['Player', 'Team', 'Fantasy Points', 'W', 'SV', 'SO', 'SV%', 'GAA']
    goalies_display = goalies[goalie_cols].copy()
    goalies_display['Player Type'] = 'Goalie'
    goalies_display['Pos'] = 'G'
    
    # Add missing columns to goalies to match skaters structure
    for col in ['G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK']:
        goalies_display[col] = 0
    
    # Add missing goalie columns to skaters
    for col in ['W', 'SV', 'SO', 'SV%', 'GAA']:
        skaters_display[col] = 0
    
    # Combine and sort by Fantasy Points
    combined = pd.concat([skaters_display, goalies_display], ignore_index=True)
    combined = combined.sort_values('Fantasy Points', ascending=False).reset_index(drop=True)
    combined['Rank'] = range(1, len(combined) + 1)
    
    return combined

def style_dataframe_for_fantasy_points(df):
    """Style the dataframe to highlight Fantasy Points column"""
    def highlight_fantasy_points(val):
        if val.name == 'Fantasy Points':
            return ['background-color: #f0f9ff; font-weight: bold; font-size: 24px; color: #1e40af' for _ in val]
        else:
            return ['' for _ in val]
    
    return df.style.apply(highlight_fantasy_points, axis=0)

def main():
    # Centered and underlined header
    st.markdown("""
    <h1 style='text-align: center; text-decoration: underline; margin-bottom: 30px;'>
    🏒 NHL Fantasy Draft Tool
    </h1>
    """, unsafe_allow_html=True)
    
    # Custom CSS for Fantasy Points column styling (2nd column)
    st.markdown("""
    <style>
    /* Simple approach - target all 2nd column cells */
    table td:nth-child(2), table th:nth-child(2) {
        font-weight: bold !important;
        text-align: left !important;
        font-size: 20px !important;
        background-color: #f0f9ff !important;
        color: #1e40af !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load data
    skaters, goalies = load_data()
    
    if skaters is None or goalies is None:
        st.error("Could not load data files. Please check that the CSV files exist in the 'data' folder.")
        return
    
    # Create fantasy scoring inputs
    scoring = create_fantasy_scoring_inputs()
    
    # Add the RUN button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        run_calculation = st.button("🏆 RUN FANTASY CALCULATION", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Only calculate and display results when button is pressed
    if run_calculation or 'fantasy_calculated' in st.session_state:
        # Set session state to remember calculation was run
        st.session_state['fantasy_calculated'] = True
        
        # Calculate fantasy points
        skaters_with_points = calculate_fantasy_points(skaters, scoring, 'skater')
        goalies_with_points = calculate_fantasy_points(goalies, scoring, 'goalie')
        
        # Create combined rankings
        combined_rankings = create_combined_rankings(skaters_with_points, goalies_with_points)
        
        # Display results
        st.success("✅ Fantasy points calculated successfully!")
        
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Players Ranked", f"{len(combined_rankings):,}")
        with col2:
            top_player = combined_rankings.iloc[0]
            st.metric("Top Player", f"{top_player['Player']}")
        with col3:
            st.metric("Top Fantasy Points", f"{top_player['Fantasy Points']:.1f}")
        with col4:
            top_goalie = combined_rankings[combined_rankings['Pos'] == 'G'].iloc[0]
            st.metric("Top Goalie", f"{top_goalie['Player']}")
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🏆 All Players", "🏒 Forwards", "🛡️ Defense", "⬅️ LW", "➡️ RW", "🥅 Goalies", "📊 Analysis"])
        
        with tab1:
            st.subheader("🏆 Complete Fantasy Rankings - All Players")
            st.markdown("**Ranked from highest to lowest fantasy points**")
            
            # Display options
            col1, col2 = st.columns(2)
            with col1:
                show_top = st.selectbox("Show top:", [50, 100, 200, "All"], index=1)
            with col2:
                position_filter = st.multiselect("Filter by position:", 
                                                sorted(combined_rankings['Pos'].unique()), 
                                                default=[])
            
            # Apply filters
            display_data = combined_rankings.copy()
            if position_filter:
                display_data = display_data[display_data['Pos'].isin(position_filter)]
            
            if show_top != "All":
                display_data = display_data.head(show_top)
            
            # Display the ranking table with ALL requested columns
            st.dataframe(
                display_data[['Rank', 'Fantasy Points', 'Player', 'Team', 'Pos', 
                             'G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK', 
                             'W', 'SV', 'SO', 'SV%', 'GAA']],
                width='stretch',
                height=600,
                hide_index=True,
                column_config={
                    "Fantasy Points": st.column_config.NumberColumn(
                        "Fantasy Points",
                        help="Total fantasy points based on your scoring settings",
                        format="%.1f",
                        width="medium"
                    )
                }
            )
            
            # Download button
            csv = combined_rankings.to_csv(index=False)
            st.download_button(
                label="📥 Download Complete Rankings as CSV",
                data=csv,
                file_name=f'nhl_fantasy_rankings_{len(combined_rankings)}_players.csv',
                mime='text/csv'
            )
        
        with tab2:
            st.subheader("🏒 Forwards Rankings")
            skaters_only = combined_rankings[combined_rankings['Player Type'] == 'Skater'].reset_index(drop=True)
            skaters_only['Skater Rank'] = range(1, len(skaters_only) + 1)
            
            st.dataframe(
                skaters_only[['Skater Rank', 'Fantasy Points', 'Player', 'Team', 'Pos', 
                             'G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK']],
                width='stretch',
                height=600,
                hide_index=True
            )
            
            # Top skater chart
            fig = px.bar(
                skaters_only.head(15),
                x='Fantasy Points',
                y='Player',
                orientation='h',
                title="Top 15 Skaters by Fantasy Points",
                labels={'Fantasy Points': 'Fantasy Points'}
            )
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, width='stretch')
        
        with tab3:
            st.subheader("🛡️ Defensemen Rankings")
            d_only = combined_rankings[combined_rankings['Pos'] == 'D'].reset_index(drop=True)
            
            if not d_only.empty:
                d_only['D Rank'] = range(1, len(d_only) + 1)
                
                st.dataframe(
                    d_only[['D Rank', 'Fantasy Points', 'Player', 'Team', 
                            'G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK']],
                    width='stretch',
                    height=600,
                    hide_index=True
                )
                
                # Top D chart
                if len(d_only) >= 10:
                    chart_data = d_only.head(15)
                else:
                    chart_data = d_only
                
                fig = px.bar(
                    chart_data,
                    x='Fantasy Points',
                    y='Player',
                    orientation='h',
                    title="Top Defensemen by Fantasy Points",
                    labels={'Fantasy Points': 'Fantasy Points'}
                )
                fig.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig, width='stretch')
                
                st.metric(f"Total Defensemen", f"{len(d_only)}")
            else:
                st.warning("No Defensemen found in the data.")
        
        with tab4:
            st.subheader("⬅️ Left Wingers Rankings")
            lw_only = combined_rankings[combined_rankings['Pos'] == 'LW'].reset_index(drop=True)
            
            if not lw_only.empty:
                lw_only['LW Rank'] = range(1, len(lw_only) + 1)
                
                st.dataframe(
                    lw_only[['LW Rank', 'Fantasy Points', 'Player', 'Team', 
                             'G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK']],
                    width='stretch',
                    height=600,
                    hide_index=True
                )
                
                # Top LW chart
                if len(lw_only) >= 10:
                    chart_data = lw_only.head(15)
                else:
                    chart_data = lw_only
                
                fig = px.bar(
                    chart_data,
                    x='Fantasy Points',
                    y='Player',
                    orientation='h',
                    title="Top Left Wingers by Fantasy Points",
                    labels={'Fantasy Points': 'Fantasy Points'}
                )
                fig.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig, width='stretch')
                
                st.metric(f"Total Left Wingers", f"{len(lw_only)}")
            else:
                st.warning("No Left Wingers found in the data.")
        
        with tab5:
            st.subheader("➡️ Right Wingers Rankings")
            rw_only = combined_rankings[combined_rankings['Pos'] == 'RW'].reset_index(drop=True)
            
            if not rw_only.empty:
                rw_only['RW Rank'] = range(1, len(rw_only) + 1)
                
                st.dataframe(
                    rw_only[['RW Rank', 'Fantasy Points', 'Player', 'Team', 
                             'G', 'A', 'PTS', 'PIM', 'PPG', 'PPP', 'SOG', 'HIT', 'BLK']],
                    width='stretch',
                    height=600,
                    hide_index=True
                )
                
                # Top RW chart
                if len(rw_only) >= 10:
                    chart_data = rw_only.head(15)
                else:
                    chart_data = rw_only
                
                fig = px.bar(
                    chart_data,
                    x='Fantasy Points',
                    y='Player',
                    orientation='h',
                    title="Top Right Wingers by Fantasy Points",
                    labels={'Fantasy Points': 'Fantasy Points'}
                )
                fig.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig, width='stretch')
                
                st.metric(f"Total Right Wingers", f"{len(rw_only)}")
            else:
                st.warning("No Right Wingers found in the data.")
        
        with tab6:
            st.subheader("🥅 Goalies Rankings")
            goalies_only = combined_rankings[combined_rankings['Player Type'] == 'Goalie'].reset_index(drop=True)
            goalies_only['Goalie Rank'] = range(1, len(goalies_only) + 1)
            
            st.dataframe(
                goalies_only[['Goalie Rank', 'Fantasy Points', 'Player', 'Team', 
                             'W', 'SV', 'SO', 'SV%', 'GAA']],
                width='stretch',
                height=400,
                hide_index=True
            )
            
            # Top goalie chart
            fig = px.bar(
                goalies_only.head(15),
                x='Fantasy Points',
                y='Player',
                orientation='h',
                title="Top 15 Goalies by Fantasy Points",
                labels={'Fantasy Points': 'Fantasy Points'}
            )
            fig.update_yaxes(categoryorder='total ascending')
            st.plotly_chart(fig, width='stretch')
        
        with tab7:
            st.subheader("📊 Fantasy Points Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Position breakdown
                st.markdown("**Fantasy Points by Position**")
                pos_stats = combined_rankings.groupby('Pos')['Fantasy Points'].agg(['count', 'mean', 'max']).reset_index()
                pos_stats.columns = ['Position', 'Player Count', 'Average Points', 'Max Points']
                pos_stats = pos_stats.sort_values('Average Points', ascending=False)
                
                st.dataframe(pos_stats, width='stretch', hide_index=True)
                
                # Position chart
                fig = px.bar(
                    pos_stats,
                    x='Position',
                    y='Average Points',
                    title="Average Fantasy Points by Position"
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                # Team breakdown (top 10 teams)
                st.markdown("**Top 10 Teams by Total Fantasy Points**")
                team_stats = combined_rankings.groupby('Team')['Fantasy Points'].sum().reset_index()
                team_stats.columns = ['Team', 'Total Fantasy Points']
                team_stats = team_stats.sort_values('Total Fantasy Points', ascending=False).head(10)
                
                st.dataframe(team_stats, width='stretch', hide_index=True)
                
                # Team chart
                fig = px.bar(
                    team_stats,
                    x='Total Fantasy Points',
                    y='Team',
                    orientation='h',
                    title="Top 10 Teams by Total Fantasy Points"
                )
                fig.update_yaxes(categoryorder='total ascending')
                st.plotly_chart(fig, width='stretch')
    
    else:
        st.info("👆 Set your fantasy scoring values above, then click the **RUN FANTASY CALCULATION** button to see your personalized player rankings!")
        
        # Show preview of available data
        st.markdown("### 📋 Data Preview")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Skaters Available:**")
            st.metric("Total Skaters", f"{len(skaters):,}")
            st.dataframe(skaters[['Player', 'Team', 'Pos', 'G', 'A', 'PTS']].head(10), width='stretch', hide_index=True)
        
        with col2:
            st.markdown("**Goalies Available:**")
            st.metric("Total Goalies", f"{len(goalies):,}")
            st.dataframe(goalies[['Player', 'Team', 'W', 'SV%', 'GAA']].head(10), width='stretch', hide_index=True)

if __name__ == "__main__":
    main()