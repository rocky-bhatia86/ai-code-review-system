#!/usr/bin/env python3
"""
Flask API Server for EDA Storage Cost Optimization Dashboard
Wraps the eda_cost_optimization_agent.py to provide REST API endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import json
import subprocess
import tempfile
from datetime import datetime
import re

# Add the agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_adhoc_analysis_agent'))

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

def run_agent_command(command):
    """Run the cost optimization agent with a given command"""
    try:
        # Change to the agent directory
        agent_dir = os.path.join(os.path.dirname(__file__), 'ai_adhoc_analysis_agent')
        print(f"📁 Working directory: {agent_dir}")
        print(f"⚡ Executing command: {command}")
        
        # Check if the agent file exists
        agent_file = os.path.join(agent_dir, 'eda_cost_optimization_agent.py')
        if not os.path.exists(agent_file):
            return {
                'success': False,
                'error': f'Agent file not found: {agent_file}',
                'output': None,
                'return_code': -1
            }
        
        print(f"✅ Agent file found: {agent_file}")
        
        try:
            print("🚀 Starting agent subprocess...")
            # Run the agent with the command - shorter timeout for testing
            result = subprocess.run([
                'python3', 'eda_cost_optimization_agent.py'
            ], 
            input=command + '\nexit\n',
            cwd=agent_dir,
            capture_output=True,
            text=True,
            timeout=60  # Reduced to 1 minute for faster testing
            )
            
            print(f"✅ Agent completed with return code: {result.returncode}")
            print(f"📤 STDOUT length: {len(result.stdout)} chars")
            print(f"📤 STDERR length: {len(result.stderr)} chars")
            
            if result.stdout:
                print("📋 First 500 chars of output:")
                print(result.stdout[:500])
            
            if result.stderr:
                print("❌ STDERR:")
                print(result.stderr)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None,
                'return_code': result.returncode
            }
            
        except Exception as e:
            print(f"💥 Exception during agent execution: {str(e)}")
            raise
                
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out after 5 minutes',
            'output': None,
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'output': None,
            'return_code': -1
        }

def parse_agent_output(output):
    """Parse the agent output to extract structured data"""
    try:
        data = {
            'database_name': None,
            'total_table_count': 0,
            'never_accessed_count': 0,
            'accessed_count': 0,
            'unused_monthly_cost': 0,
            'unused_annual_cost': 0,
            'archive_annual_savings': 0,
            'total_hot_size_bytes': 0,
            'total_cool_size_bytes': 0,
            'total_cold_size_bytes': 0,
            'analysis_timestamp': datetime.now().isoformat(),
            'recommendations': []
        }
        
        # Extract database name - prefer from DATABASE: line, handling ANSI color codes
        db_match = re.search(r"DATABASE:\s*([^\n\r\x1b]+)", output, re.IGNORECASE)
        if db_match:
            # Clean up any ANSI escape sequences and whitespace
            db_name = re.sub(r'\x1b\[[0-9;]*m', '', db_match.group(1)).strip()
            data['database_name'] = db_name
        else:
            # Fallback to the first database reference
            db_match = re.search(r"database['\s]+(['\w\._]+)", output, re.IGNORECASE)
            if db_match:
                data['database_name'] = db_match.group(1).strip("'\"")
        
        # Extract table counts from the TOTAL DATABASE COSTS section specifically
        # Look for the pattern after "TOTAL DATABASE COSTS:" to avoid picking up wrong values
        total_costs_section = re.search(r'TOTAL DATABASE COSTS:.*?Row\([^)]+total_table_count=(\d+)[^)]+never_accessed_count=(\d+)[^)]+accessed_count=(\d+)', output, re.IGNORECASE | re.DOTALL)
        if total_costs_section:
            data['total_table_count'] = int(total_costs_section.group(1))
            data['never_accessed_count'] = int(total_costs_section.group(2))
            data['accessed_count'] = int(total_costs_section.group(3))
        else:
            # Fallback to individual patterns if section not found
            total_tables_match = re.search(r'total_table_count=(\d+)', output, re.IGNORECASE)
            if total_tables_match:
                data['total_table_count'] = int(total_tables_match.group(1))
            
            never_accessed_match = re.search(r'never_accessed_count=(\d+)', output, re.IGNORECASE)
            if never_accessed_match:
                data['never_accessed_count'] = int(never_accessed_match.group(1))
            
            accessed_match = re.search(r'accessed_count=(\d+)', output, re.IGNORECASE)
            if accessed_match:
                data['accessed_count'] = int(accessed_match.group(1))
        
        # Count actual tables from the UNUSED TABLES ONLY section (most reliable)
        unused_tables_section = re.search(r'UNUSED TABLES ONLY:(.*?)(?:COST SAVINGS|$)', output, re.IGNORECASE | re.DOTALL)
        if unused_tables_section:
            unused_section_text = unused_tables_section.group(1)
            # Count all Row(table='table_name') entries
            table_rows = re.findall(r"Row\(table='([^']+)'\)", unused_section_text, re.IGNORECASE)
            if table_rows:
                data['never_accessed_count'] = len(table_rows)
                # Fix accessed_count calculation
                if data['total_table_count'] > 0:
                    data['accessed_count'] = data['total_table_count'] - data['never_accessed_count']
        
        # Fallback: try to parse from savings analysis format: unused_table_count=15
        if data['never_accessed_count'] == 0:
            unused_count_sql_match = re.search(r'unused_table_count=(\d+)', output, re.IGNORECASE)
            if unused_count_sql_match:
                data['never_accessed_count'] = int(unused_count_sql_match.group(1))
        
        # Fallback: Try to parse from text format: "X unused tables"
        if data['never_accessed_count'] == 0:
            unused_tables_text_match = re.search(r'(\d+)\s+unused tables', output, re.IGNORECASE)
            if unused_tables_text_match:
                data['never_accessed_count'] = int(unused_tables_text_match.group(1))
        
        # FIRST: Extract total storage sizes from SQL result format  
        hot_size_match = re.search(r'total_hot_size_bytes=(\d+)', output, re.IGNORECASE)
        if hot_size_match:
            data['total_hot_size_bytes'] = int(hot_size_match.group(1))
        
        cool_size_match = re.search(r'total_cool_size_bytes=(\d+)', output, re.IGNORECASE)
        if cool_size_match:
            data['total_cool_size_bytes'] = int(cool_size_match.group(1))
        
        cold_size_match = re.search(r'total_cold_size_bytes=(\d+)', output, re.IGNORECASE)
        if cold_size_match:
            data['total_cold_size_bytes'] = int(cold_size_match.group(1))

        # SECOND: Extract unused storage sizes from the simple query results
        # Look for pattern: Row(unused_cold_size_bytes=X, unused_hot_size_bytes=Y, unused_cool_size_bytes=Z, unused_table_count=W)
        unused_pattern = r'unused_cold_size_bytes=(\d+).*?unused_hot_size_bytes=(\d+).*?unused_cool_size_bytes=(\d+)'
        unused_match = re.search(unused_pattern, output, re.IGNORECASE | re.DOTALL)
        
        if unused_match:
            data['unused_cold_size_bytes'] = int(unused_match.group(1))
            data['unused_hot_size_bytes'] = int(unused_match.group(2))
            data['unused_cool_size_bytes'] = int(unused_match.group(3))
        else:
            # Fallback: try individual patterns
            cold_match = re.search(r'unused_cold_size_bytes=(\d+)', output, re.IGNORECASE)
            hot_match = re.search(r'unused_hot_size_bytes=(\d+)', output, re.IGNORECASE)
            cool_match = re.search(r'unused_cool_size_bytes=(\d+)', output, re.IGNORECASE)
            
            data['unused_cold_size_bytes'] = int(cold_match.group(1)) if cold_match else 0
            data['unused_hot_size_bytes'] = int(hot_match.group(1)) if hot_match else 0
            data['unused_cool_size_bytes'] = int(cool_match.group(1)) if cool_match else 0
            
            # Final fallback: proportional calculation if parsing completely fails
            if (data['unused_cold_size_bytes'] == 0 and data['unused_hot_size_bytes'] == 0 and 
                data['unused_cool_size_bytes'] == 0 and data['never_accessed_count'] > 0 and 
                data['total_table_count'] > 0):
                
                unused_ratio = data['never_accessed_count'] / data['total_table_count']
                data['unused_hot_size_bytes'] = int(data.get('total_hot_size_bytes', 0) * unused_ratio)
                data['unused_cool_size_bytes'] = int(data.get('total_cool_size_bytes', 0) * unused_ratio)
                data['unused_cold_size_bytes'] = int(data.get('total_cold_size_bytes', 0) * unused_ratio)
        
        # Calculate costs from unused storage data for consistency
        unused_hot_gb = data.get('unused_hot_size_bytes', 0) / (1024**3)
        unused_cool_gb = data.get('unused_cool_size_bytes', 0) / (1024**3)
        unused_cold_gb = data.get('unused_cold_size_bytes', 0) / (1024**3)
        
        # Use correct Azure pricing: Hot $7.600/TB, Cool $4.522/TB, Cold $1.434/TB
        hot_monthly_cost = unused_hot_gb * 0.007600
        cool_monthly_cost = unused_cool_gb * 0.004522  
        cold_monthly_cost = unused_cold_gb * 0.001434
        
        data['unused_monthly_cost'] = hot_monthly_cost + cool_monthly_cost + cold_monthly_cost
        data['unused_annual_cost'] = data['unused_monthly_cost'] * 12
        data['archive_annual_savings'] = data['unused_annual_cost'] * 0.8  # 80% savings moving to archive
        
        # Extract recommendations from output
        recommendations = []
        
        # Only add recommendations if there are actually unused tables
        if data['never_accessed_count'] > 0:
            if 'delete' in output.lower() or data['unused_annual_cost'] > 0:
                recommendations.append(f"Delete {data['never_accessed_count']} unused tables to save ${data['unused_annual_cost']:,.2f} annually")
            if 'archive' in output.lower():
                recommendations.append("Consider moving unused tables to Archive tier for cost savings")
            if 'priority' in output.lower() or data['unused_annual_cost'] > 100000:
                recommendations.append("High priority action required due to significant cost impact")
        else:
            # No unused tables found
            if 'no unused tables' in output.lower() or data['never_accessed_count'] == 0:
                recommendations.append("✅ No unused tables found - database is optimally utilized")
                recommendations.append("💡 Consider running analysis on other databases or with different thresholds")
            else:
                recommendations.append("Analysis completed - check raw output for details")
        
        data['recommendations'] = recommendations
        
        return data
        
    except Exception as e:
        print(f"Error parsing output: {e}")
        return None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'EDA Storage Cost Optimization API'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_database():
    """Main analysis endpoint"""
    try:
        print("🔥 API /analyze endpoint called")
        data = request.get_json()
        print(f"📥 Request data: {data}")
        
        database_name = data.get('database_name', 'darwin_max')
        analysis_type = data.get('analysis_type', 'comprehensive')
        days_threshold = data.get('days_threshold', 90)
        
        print(f"🎯 Parameters: db={database_name}, type={analysis_type}, threshold={days_threshold}")
        
        # Build command based on analysis type
        if analysis_type == 'unused':
            command = f"find unused tables in database {database_name}"
        elif analysis_type == 'costs':
            command = f"analyze database {database_name}"
        elif analysis_type == 'optimization':
            command = f"storage_optimization {database_name}"
        elif analysis_type == 'savings':
            command = f"calculate savings for {database_name} {days_threshold}"
        else:
            command = f"analyze database {database_name}"
        
        print(f"📋 Final command: {command}")
        
        # Run the agent
        print("🏃 Running agent command...")
        result = run_agent_command(command)
        print(f"🏁 Agent result: success={result['success']}, return_code={result.get('return_code')}")
        
        if not result['success']:
            error_msg = result['error'] or f"Agent failed with return code {result.get('return_code')}"
            print(f"❌ Agent failed: {error_msg}")
            return jsonify({
                'error': error_msg,
                'raw_output': result.get('output'),
                'success': False
            }), 500
        
        print("🔍 Parsing agent output...")
        # Parse the output
        parsed_data = parse_agent_output(result['output'])
        
        if parsed_data is None:
            print("⚠️ Could not parse output, returning raw result")
            # Fallback with raw output
            return jsonify({
                'database_name': database_name,
                'raw_output': result['output'],
                'analysis_type': analysis_type,
                'command': command,
                'success': True,
                'parsed': False
            })
        
        # Always include raw output for debugging
        parsed_data['raw_output'] = result['output']
        
        print("✅ Successfully parsed output")
        # Add metadata and preserve user input
        parsed_data['analysis_type'] = analysis_type
        parsed_data['command'] = command
        parsed_data['success'] = True
        parsed_data['parsed'] = True
        parsed_data['user_input_name'] = database_name  # Preserve the original user input
        
        return jsonify(parsed_data)
        
    except Exception as e:
        print(f"💥 API Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/databases', methods=['GET'])
def list_databases():
    """List available databases"""
    try:
        # This would typically query your data source
        # For now, return common database names
        databases = [
            'darwin_max',
            'darwin_raw',
            'dpaas_uccatalog_prd.darwin_max',
            'dpaas_uccatalog_prd.darwin_raw'
        ]
        
        return jsonify({
            'databases': databases,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    print("🚀 Starting EDA Storage Cost Optimization API Server...")
    print("📊 Dashboard API available at: http://localhost:5001")
    print("🔧 Health check: http://localhost:5001/api/health")
    print("💡 Connect your React dashboard to: http://localhost:5001/api/analyze")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 