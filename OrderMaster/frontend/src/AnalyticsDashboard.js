import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

// Register the components you are using from Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const AnalyticsDashboard = () => {
  // State to hold all our data from the API
  const [keyMetrics, setKeyMetrics] = useState(null);
  const [topProductsData, setTopProductsData] = useState(null);
  const [mostOrderedData, setMostOrderedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for the date filter
  const [dateFilter, setDateFilter] = useState('this_month');

  // This function runs when the component loads or the dateFilter changes
  useEffect(() => {
    const fetchAnalyticsData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch data from your Django API using the current date filter
        const response = await axios.get(`/api/analytics/?date_filter=${dateFilter}`);
        const data = response.data;

        // Set the data into our state variables
        setKeyMetrics(data.key_metrics);

        setTopProductsData({
            labels: data.top_products_by_type.labels,
            datasets: data.top_products_by_type.datasets,
        });

        setMostOrderedData({
            labels: data.most_ordered_items.labels,
            datasets: [{
                label: 'Quantity Sold',
                data: data.most_ordered_items.data,
                backgroundColor: ['#ff8100', '#ff9f40', '#ffbd6e', '#ffda9a', '#ffedc9'],
                borderColor: '#fff',
                borderWidth: 2,
            }]
        });

      } catch (err) {
        setError('Failed to load data. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyticsData();
  }, [dateFilter]); // The effect re-runs whenever 'dateFilter' changes

  // Chart options to fix the plot size issue
  const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false, // This is key to controlling size with CSS
  };
    
  const barChartOptions = {
    ...commonChartOptions,
    indexAxis: 'y', // Horizontal bar chart
    plugins: {
      title: { display: false },
    },
    scales: {
      x: { stacked: true, ticks: { callback: (value) => `${value}%` } },
      y: { stacked: true },
    },
  };


  if (loading) return <div className="loading">Loading Analytics...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="analytics-container">
      <header className="analytics-header">
        <h3>Analytics Dashboard</h3>
        <select value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="date-filter">
            <option value="today">Today</option>
            <option value="this_week">This Week</option>
            <option value="this_month">This Month</option>
        </select>
      </header>
      
      {keyMetrics && (
        <div className="kpi-grid">
            <div className="kpi-card"><h5>Total Revenue</h5><p>₹{keyMetrics.total_revenue}</p></div>
            <div className="kpi-card"><h5>Total Orders</h5><p>{keyMetrics.total_orders}</p></div>
            <div className="kpi-card"><h5>Average Order Value</h5><p>₹{keyMetrics.average_order_value}</p></div>
        </div>
      )}

      <div className="chart-grid">
        <div className="chart-wrapper large">
          <h5>Top 5 Products by Order Type</h5>
          <div className="chart-inner">
            {topProductsData && <Bar data={topProductsData} options={barChartOptions} />}
          </div>
        </div>
        <div className="chart-wrapper small">
          <h5>Most Ordered Items</h5>
          <div className="chart-inner">
            {mostOrderedData && <Doughnut data={mostOrderedData} options={commonChartOptions} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
