import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Upload,
  Transform,
  CheckCircle,
  Error,
  Schedule,
  TrendingUp,
  Description,
  SmartToy
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

import { apiService } from '../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  // Fetch dashboard data
  const { data: conversionJobs = [] } = useQuery(
    'conversionJobs',
    () => apiService.getConversionJobs(),
    { refetchInterval: 5000 }
  );

  const { data: templates = [] } = useQuery(
    'templates',
    () => apiService.getTemplates()
  );

  const { data: templateStats } = useQuery(
    'templateStats',
    () => apiService.getTemplateStats()
  );

  // Calculate stats
  const recentJobs = conversionJobs.slice(0, 5);
  const completedJobs = conversionJobs.filter(job => job.status === 'completed');
  const failedJobs = conversionJobs.filter(job => job.status === 'failed');
  const pendingJobs = conversionJobs.filter(job => job.status === 'pending' || job.status === 'processing');

  // Chart data
  const statusData = [
    { name: 'Completed', value: completedJobs.length, color: '#4caf50' },
    { name: 'Failed', value: failedJobs.length, color: '#f44336' },
    { name: 'Pending', value: pendingJobs.length, color: '#ff9800' },
  ];

  const dailyStats = [
    { day: 'Mon', conversions: 12 },
    { day: 'Tue', conversions: 19 },
    { day: 'Wed', conversions: 8 },
    { day: 'Thu', conversions: 15 },
    { day: 'Fri', conversions: 22 },
    { day: 'Sat', conversions: 5 },
    { day: 'Sun', conversions: 3 },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'failed': return <Error />;
      case 'processing': return <Schedule />;
      default: return <Schedule />;
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Quick Stats */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Transform color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Conversions</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {conversionJobs.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All time
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Success Rate</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {conversionJobs.length > 0 
                  ? Math.round((completedJobs.length / conversionJobs.length) * 100)
                  : 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {completedJobs.length}/{conversionJobs.length} successful
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Description color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Templates</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {templates.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Available templates
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Schedule color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">Processing</Typography>
              </Box>
              <Typography variant="h4" color="warning.main">
                {pendingJobs.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Jobs in queue
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="contained"
                  startIcon={<Upload />}
                  fullWidth
                  onClick={() => navigate('/convert')}
                  sx={{ py: 2 }}
                >
                  Convert PDF
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  startIcon={<Description />}
                  fullWidth
                  onClick={() => navigate('/templates/new')}
                  sx={{ py: 2 }}
                >
                  New Template
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  startIcon={<SmartToy />}
                  fullWidth
                  onClick={() => navigate('/ml')}
                  sx={{ py: 2 }}
                >
                  ML Features
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  variant="outlined"
                  startIcon={<TrendingUp />}
                  fullWidth
                  onClick={() => navigate('/templates')}
                  sx={{ py: 2 }}
                >
                  View Templates
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Charts */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Daily Conversions
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyStats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="conversions" fill="#1976d2" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Conversion Status
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Conversions
            </Typography>
            {recentJobs.length > 0 ? (
              <List>
                {recentJobs.map((job, index) => (
                  <React.Fragment key={job.job_id}>
                    <ListItem>
                      <ListItemIcon>
                        {getStatusIcon(job.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={job.pdf_filename}
                        secondary={`Template: ${job.template_used || 'Auto-detect'}`}
                      />
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status) as any}
                        size="small"
                      />
                    </ListItem>
                    {index < recentJobs.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                No recent conversions
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Template Stats */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Template Statistics
            </Typography>
            {templateStats ? (
              <Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Templates
                  </Typography>
                  <Typography variant="h5">
                    {templateStats.total_templates}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Average Success Rate
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={templateStats.average_success_rate * 100}
                      sx={{ flexGrow: 1, mr: 1 }}
                    />
                    <Typography variant="body2">
                      {Math.round(templateStats.average_success_rate * 100)}%
                    </Typography>
                  </Box>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Most Used Template
                  </Typography>
                  <Typography variant="body1">
                    {templateStats.most_used_template || 'None'}
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                Loading template statistics...
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;