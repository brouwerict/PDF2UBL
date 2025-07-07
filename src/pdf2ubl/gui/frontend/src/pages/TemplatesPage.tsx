import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const TemplatesPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Templates
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Template management interface will be implemented here.
        </Typography>
      </Paper>
    </Box>
  );
};

export default TemplatesPage;