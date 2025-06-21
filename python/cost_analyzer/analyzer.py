#!/usr/bin/env python3
"""
Multi-Cloud Cost Analyzer
Analyzes and reports on infrastructure costs across AWS, Azure, and GCP
"""

import json
import logging
import boto3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from azure.identity import DefaultAzureCredential
from azure.mgmt.consumption import ConsumptionManagementClient
from google.cloud import billing


@dataclass
class CostData:
    """Data class for cost information"""
    service: str
    cost: float
    currency: str
    date: datetime
    cloud_provider: str
    resource_id: Optional[str] = None
    tags: Optional[Dict] = None


class CloudCostAnalyzer:
    """Base class for cloud cost analysis"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def get_cost_data(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Abstract method to get cost data"""
        raise NotImplementedError


class AWSCostAnalyzer(CloudCostAnalyzer):
    """AWS Cost Explorer integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = boto3.client('ce', region_name=config.get('region', 'us-east-1'))
    
    def get_cost_data(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get AWS cost data using Cost Explorer API"""
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            cost_data = []
            for result in response['ResultsByTime']:
                date = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d')
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    currency = group['Metrics']['BlendedCost']['Unit']
                    
                    cost_data.append(CostData(
                        service=service,
                        cost=cost,
                        currency=currency,
                        date=date,
                        cloud_provider='AWS'
                    ))
            
            return cost_data
            
        except Exception as e:
            self.logger.error(f"Error fetching AWS cost data: {e}")
            return []


class AzureCostAnalyzer(CloudCostAnalyzer):
    """Azure Cost Management integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.credential = DefaultAzureCredential()
        self.client = ConsumptionManagementClient(
            self.credential, 
            config['subscription_id']
        )
    
    def get_cost_data(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get Azure cost data"""
        try:
            # Simplified example - actual implementation would use Azure API
            cost_data = []
            # Mock data for demonstration
            services = ['Compute', 'Storage', 'Networking', 'Database']
            
            current_date = start_date
            while current_date <= end_date:
                for service in services:
                    cost_data.append(CostData(
                        service=service,
                        cost=round(50 + (hash(service + str(current_date)) % 100), 2),
                        currency='USD',
                        date=current_date,
                        cloud_provider='Azure'
                    ))
                current_date += timedelta(days=1)
            
            return cost_data
            
        except Exception as e:
            self.logger.error(f"Error fetching Azure cost data: {e}")
            return []


class GCPCostAnalyzer(CloudCostAnalyzer):
    """Google Cloud Platform cost analysis"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.client = billing.CloudBillingClient()
        self.project_id = config['project_id']
    
    def get_cost_data(self, start_date: datetime, end_date: datetime) -> List[CostData]:
        """Get GCP cost data"""
        try:
            # Simplified example - actual implementation would use GCP Billing API
            cost_data = []
            services = ['Compute Engine', 'Cloud Storage', 'BigQuery', 'Cloud SQL']
            
            current_date = start_date
            while current_date <= end_date:
                for service in services:
                    cost_data.append(CostData(
                        service=service,
                        cost=round(30 + (hash(service + str(current_date)) % 80), 2),
                        currency='USD',
                        date=current_date,
                        cloud_provider='GCP'
                    ))
                current_date += timedelta(days=1)
            
            return cost_data
            
        except Exception as e:
            self.logger.error(f"Error fetching GCP cost data: {e}")
            return []


class MultiCloudCostAnalyzer:
    """Main analyzer that aggregates costs across all cloud providers"""
    
    def __init__(self, config_file: str = 'config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.analyzers = {
            'aws': AWSCostAnalyzer(self.config.get('aws', {})),
            'azure': AzureCostAnalyzer(self.config.get('azure', {})),
            'gcp': GCPCostAnalyzer(self.config.get('gcp', {}))
        }
        
        self.logger = logging.getLogger(__name__)
    
    def generate_cost_report(self, days_back: int = 30) -> pd.DataFrame:
        """Generate comprehensive cost report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        all_cost_data = []
        
        for provider, analyzer in self.analyzers.items():
            try:
                cost_data = analyzer.get_cost_data(start_date, end_date)
                all_cost_data.extend(cost_data)
                self.logger.info(f"Retrieved {len(cost_data)} cost records from {provider}")
            except Exception as e:
                self.logger.error(f"Failed to get data from {provider}: {e}")
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame([{
            'date': item.date,
            'cloud_provider': item.cloud_provider,
            'service': item.service,
            'cost': item.cost,
            'currency': item.currency
        } for item in all_cost_data])
        
        return df
    
    def get_cost_summary(self, df: pd.DataFrame) -> Dict:
        """Generate cost summary statistics"""
        if df.empty:
            return {"error": "No cost data available"}
        
        summary = {
            'total_cost': df['cost'].sum(),
            'average_daily_cost': df.groupby('date')['cost'].sum().mean(),
            'cost_by_provider': df.groupby('cloud_provider')['cost'].sum().to_dict(),
            'cost_by_service': df.groupby('service')['cost'].sum().sort_values(ascending=False).head(10).to_dict(),
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            }
        }
        
        return summary
    
    def detect_anomalies(self, df: pd.DataFrame, threshold: float = 2.0) -> List[Dict]:
        """Detect cost anomalies using statistical analysis"""
        if df.empty:
            return []
        
        daily_costs = df.groupby(['date', 'cloud_provider'])['cost'].sum().reset_index()
        anomalies = []
        
        for provider in daily_costs['cloud_provider'].unique():
            provider_data = daily_costs[daily_costs['cloud_provider'] == provider]
            mean_cost = provider_data['cost'].mean()
            std_cost = provider_data['cost'].std()
            
            for _, row in provider_data.iterrows():
                z_score = (row['cost'] - mean_cost) / std_cost if std_cost > 0 else 0
                
                if abs(z_score) > threshold:
                    anomalies.append({
                        'date': row['date'].strftime('%Y-%m-%d'),
                        'provider': row['cloud_provider'],
                        'cost': row['cost'],
                        'expected_range': f"{mean_cost - threshold*std_cost:.2f} - {mean_cost + threshold*std_cost:.2f}",
                        'severity': 'high' if abs(z_score) > 3 else 'medium'
                    })
        
        return sorted(anomalies, key=lambda x: x['date'], reverse=True)
    
    def generate_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate cost optimization recommendations"""
        if df.empty:
            return ["No data available for recommendations"]
        
        recommendations = []
        
        # High-cost services
        top_services = df.groupby('service')['cost'].sum().sort_values(ascending=False).head(3)
        for service, cost in top_services.items():
            recommendations.append(f"Review {service} usage - accounts for ${cost:.2f} in costs")
        
        # Provider distribution
        provider_costs = df.groupby('cloud_provider')['cost'].sum()
        if len(provider_costs) > 1:
            max_provider = provider_costs.idxmax()
            recommendations.append(f"Consider workload distribution - {max_provider} accounts for {(provider_costs[max_provider]/provider_costs.sum()*100):.1f}% of costs")
        
        # Daily trend analysis
        daily_trend = df.groupby('date')['cost'].sum()
        if len(daily_trend) > 7:
            recent_avg = daily_trend.tail(7).mean()
            overall_avg = daily_trend.mean()
            
            if recent_avg > overall_avg * 1.2:
                recommendations.append("Recent costs are 20% above average - investigate recent deployments")
        
        return recommendations


def main():
    """Main execution function"""
    try:
        analyzer = MultiCloudCostAnalyzer()
        
        # Generate cost report
        print("Generating multi-cloud cost report...")
        df = analyzer.generate_cost_report(days_back=30)
        
        if not df.empty:
            # Print summary
            summary = analyzer.get_cost_summary(df)
            print(f"\n=== COST SUMMARY ===")
            print(f"Total Cost: ${summary['total_cost']:.2f}")
            print(f"Average Daily Cost: ${summary['average_daily_cost']:.2f}")
            print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
            
            print(f"\n=== COST BY PROVIDER ===")
            for provider, cost in summary['cost_by_provider'].items():
                print(f"{provider}: ${cost:.2f}")
            
            # Detect anomalies
            anomalies = analyzer.detect_anomalies(df)
            if anomalies:
                print(f"\n=== COST ANOMALIES DETECTED ===")
                for anomaly in anomalies[:5]:  # Show top 5
                    print(f"Date: {anomaly['date']}, Provider: {anomaly['provider']}, "
                          f"Cost: ${anomaly['cost']:.2f}, Severity: {anomaly['severity']}")
            
            # Generate recommendations
            recommendations = analyzer.generate_recommendations(df)
            print(f"\n=== RECOMMENDATIONS ===")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
            
            # Save report
            df.to_csv('cost_report.csv', index=False)
            print(f"\nDetailed report saved to 'cost_report.csv'")
        
        else:
            print("No cost data available. Check your cloud provider configurations.")
    
    except Exception as e:
        print(f"Error running cost analysis: {e}")


if __name__ == "__main__":
    main()
