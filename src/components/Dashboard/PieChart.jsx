import React from 'react';
import { Pie } from '@ant-design/plots';

export const PieChart = ({ data }) => {
    console.log('PieChart data:', data); // Debug log

    const chartData = Object.entries(data || {})
        .filter(([_, value]) => value > 0)
        .map(([status, value]) => ({
            type: status,
            value: parseInt(value, 10)  // Ensure values are numbers
        }));

    console.log('Transformed chart data:', chartData); // Debug log

    if (chartData.length === 0) {
        return <div>No data available for chart</div>;
    }

    const config = {
        appendPadding: 10,
        data: chartData,
        angleField: 'value',
        colorField: 'type',
        radius: 0.8,
        label: {
            type: 'outer',
            content: '{name} ({value})'
        },
        interactions: [
            {
                type: 'element-active'
            }
        ]
    };

    return <Pie {...config} />;
}; 