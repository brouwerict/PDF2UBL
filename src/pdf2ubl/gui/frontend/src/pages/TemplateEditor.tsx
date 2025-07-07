import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const TemplateEditor: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Template Editor
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Template editing interface will be implemented here.
        </Typography>
      </Paper>
    </Box>
  );
};

export default TemplateEditor;