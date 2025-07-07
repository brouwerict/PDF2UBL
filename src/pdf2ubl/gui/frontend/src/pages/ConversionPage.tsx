import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  LinearProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Card,
  CardContent,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
} from '@mui/material';
import {
  Upload,
  CloudUpload,
  Download,
  ExpandMore,
  CheckCircle,
  Delete,
  PictureAsPdf,
  Archive,
  Refresh,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery } from 'react-query';
import { useSnackbar } from 'notistack';

import { apiService } from '../services/api';

interface BatchConversionResult {
  batch_id: string;
  job_ids: string[];
  message: string;
  jobs: any[];
}

const ConversionPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [supplierHint, setSupplierHint] = useState('');
  const [previewOnly, setPreviewOnly] = useState(false);
  const [conversionResult, setConversionResult] = useState<any>(null);
  const [previewResult, setPreviewResult] = useState<any>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [batchMode, setBatchMode] = useState(false);
  const [batchResult, setBatchResult] = useState<BatchConversionResult | null>(null);
  const [batchJobs, setBatchJobs] = useState<any[]>([]);

  // Fetch templates
  const { data: templates = [] } = useQuery('templates', apiService.getTemplates);

  // Upload mutation for conversion
  const uploadMutation = useMutation(
    (data: { file: File; templateId?: string; supplierHint?: string; previewOnly?: boolean }) =>
      apiService.uploadAndConvert(data.file, data.templateId, data.supplierHint, data.previewOnly),
    {
      onSuccess: (result) => {
        setConversionResult(result);
        enqueueSnackbar('Conversion started! Check the result below.', { variant: 'success' });
        
        // Start polling for job completion if we have a job_id
        if (result.job_id) {
          pollJobStatus(result.job_id);
        }
      },
      onError: (error: any) => {
        enqueueSnackbar(`Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  // Preview mutation
  const previewMutation = useMutation(
    (data: { file: File; templateId?: string; supplierHint?: string }) =>
      apiService.previewExtraction(data.file, data.templateId, data.supplierHint),
    {
      onSuccess: (result) => {
        setPreviewResult(result);
        enqueueSnackbar('Preview extraction completed!', { variant: 'success' });
      },
      onError: (error: any) => {
        enqueueSnackbar(`Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  // Batch conversion mutation
  const batchMutation = useMutation(
    (data: { files: File[]; templateId?: string; supplierHint?: string }) =>
      apiService.batchConvert(data.files, data.templateId, data.supplierHint),
    {
      onSuccess: (result) => {
        setBatchResult({ ...result, jobs: [] });
        enqueueSnackbar(`Batch conversion started with ${result.job_ids.length} files!`, { variant: 'success' });
        
        // Start polling for all job completions
        result.job_ids.forEach(jobId => pollJobStatus(jobId, true));
      },
      onError: (error: any) => {
        enqueueSnackbar(`Batch Error: ${error.response?.data?.detail || error.message}`, { variant: 'error' });
      },
    }
  );

  const onDrop = (acceptedFiles: File[]) => {
    if (batchMode) {
      setSelectedFiles(prev => [...prev, ...acceptedFiles]);
    } else {
      const file = acceptedFiles[0];
      if (file) {
        if (previewOnly) {
          previewMutation.mutate({
            file,
            templateId: selectedTemplate || undefined,
            supplierHint: supplierHint || undefined,
          });
        } else {
          uploadMutation.mutate({
            file,
            templateId: selectedTemplate || undefined,
            supplierHint: supplierHint || undefined,
            previewOnly: false,
          });
        }
      }
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    setBatchResult(null);
    setBatchJobs([]);
  };

  const startBatchConversion = () => {
    if (selectedFiles.length === 0) {
      enqueueSnackbar('Voeg eerst PDF bestanden toe', { variant: 'warning' });
      return;
    }

    batchMutation.mutate({
      files: selectedFiles,
      templateId: selectedTemplate || undefined,
      supplierHint: supplierHint || undefined,
    });
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: batchMode,
  });

  // Poll job status until completion
  const pollJobStatus = async (jobId: string, isBatch = false) => {
    const pollInterval = 2000; // Poll every 2 seconds
    const maxAttempts = 30; // Max 1 minute
    let attempts = 0;

    const poll = async () => {
      try {
        const jobStatus = await apiService.getConversionJob(jobId);
        
        if (isBatch) {
          setBatchJobs(prev => {
            const updated = [...prev];
            const index = updated.findIndex(job => job.job_id === jobId);
            if (index >= 0) {
              updated[index] = jobStatus;
            } else {
              updated.push(jobStatus);
            }
            return updated;
          });
        } else {
          setConversionResult(jobStatus);
        }

        if (jobStatus.status === 'completed') {
          if (!isBatch) {
            enqueueSnackbar('Conversion completed! You can now download the XML.', { variant: 'success' });
          }
          return;
        } else if (jobStatus.status === 'failed') {
          if (!isBatch) {
            enqueueSnackbar('Conversion failed!', { variant: 'error' });
          }
          return;
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, pollInterval);
        } else {
          if (!isBatch) {
            enqueueSnackbar('Conversion timeout - check status manually', { variant: 'warning' });
          }
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    };

    poll();
  };

  const downloadUBL = async () => {
    if (conversionResult?.job_id) {
      try {
        const blob = await apiService.downloadUblXml(conversionResult.job_id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${conversionResult.pdf_filename.replace('.pdf', '')}.xml`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        enqueueSnackbar('UBL XML gedownload!', { variant: 'success' });
      } catch (error) {
        enqueueSnackbar('Fout bij downloaden van XML', { variant: 'error' });
      }
    }
  };

  const downloadBatchZip = async () => {
    if (batchResult && batchJobs.length > 0) {
      try {
        const completedJobs = batchJobs.filter(job => job.status === 'completed');
        if (completedJobs.length === 0) {
          enqueueSnackbar('Geen voltooide conversies om te downloaden', { variant: 'warning' });
          return;
        }

        const jobIds = completedJobs.map(job => job.job_id);
        const blob = await apiService.downloadBatchZip(batchResult.batch_id, jobIds);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `batch_${batchResult.batch_id}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        enqueueSnackbar(`ZIP bestand met ${completedJobs.length} XML bestanden gedownload!`, { variant: 'success' });
      } catch (error) {
        enqueueSnackbar('Fout bij downloaden van ZIP bestand', { variant: 'error' });
      }
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Convert PDF to UBL XML
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Configuration
        </Typography>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={batchMode}
                  onChange={(e) => {
                    setBatchMode(e.target.checked);
                    if (!e.target.checked) {
                      clearAllFiles();
                    }
                  }}
                />
              }
              label="Batch mode (multiple files)"
            />
            {batchMode && selectedFiles.length > 0 && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<Delete />}
                onClick={clearAllFiles}
              >
                Clear All ({selectedFiles.length})
              </Button>
            )}
          </Box>

          <FormControl fullWidth>
            <InputLabel>Template (Optional)</InputLabel>
            <Select
              value={selectedTemplate}
              label="Template (Optional)"
              onChange={(e) => setSelectedTemplate(e.target.value)}
            >
              <MenuItem value="">Auto-detect</MenuItem>
              {templates.map((template) => (
                <MenuItem key={template.template_id} value={template.template_id}>
                  {template.name} ({template.supplier_name || 'Generic'})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Supplier Hint (Optional)"
            value={supplierHint}
            onChange={(e) => setSupplierHint(e.target.value)}
            placeholder="e.g., KPN, Dustin, VDX"
            helperText="Helps with template auto-detection"
            fullWidth
          />

          {!batchMode && (
            <FormControlLabel
              control={
                <Switch
                  checked={previewOnly}
                  onChange={(e) => setPreviewOnly(e.target.checked)}
                />
              }
              label="Preview only (don't generate UBL XML)"
            />
          )}
        </Box>

        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              bgcolor: 'action.hover',
              borderColor: 'primary.main',
            },
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive 
              ? (batchMode ? 'Drop PDF files here' : 'Drop the PDF here')
              : (batchMode ? 'Drag & drop PDF files' : 'Drag & drop a PDF file')
            }
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {batchMode ? 'or click to select multiple files' : 'or click to select a file'}
          </Typography>
          <Button variant="outlined" startIcon={<Upload />} sx={{ mt: 2 }}>
            {batchMode ? 'Choose Files' : 'Choose File'}
          </Button>
        </Box>

        {/* Selected Files (Batch Mode) */}
        {batchMode && selectedFiles.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Geselecteerde bestanden ({selectedFiles.length})
            </Typography>
            <Card variant="outlined">
              <CardContent sx={{ p: 2 }}>
                <List dense>
                  {selectedFiles.map((file, index) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon>
                        <PictureAsPdf color="error" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={file.name}
                        secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
                      />
                      <IconButton
                        size="small"
                        onClick={() => removeFile(index)}
                      >
                        <Delete />
                      </IconButton>
                    </ListItem>
                  ))}
                </List>
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<Upload />}
                    onClick={startBatchConversion}
                    disabled={batchMutation.isLoading}
                  >
                    Start Batch Conversion
                  </Button>
                  {batchMutation.isLoading && (
                    <LinearProgress sx={{ flexGrow: 1, mt: 1 }} />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Box>
        )}

        {(uploadMutation.isLoading || previewMutation.isLoading || batchMutation.isLoading) && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="body2" sx={{ mt: 1 }}>
              {batchMutation.isLoading ? 'Starting batch conversion...' :
               previewOnly ? 'Extracting data...' : 'Converting PDF to UBL XML...'}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Preview Result */}
      {previewResult && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            <CheckCircle color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
            Extraction Preview
          </Typography>

          <Alert severity="info" sx={{ mb: 2 }}>
            Template used: <strong>{previewResult.template_used}</strong>
          </Alert>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1">Extracted Fields</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {Object.entries(previewResult.extracted_fields).map(([key, value]) => (
                  <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      {key}:
                    </Typography>
                    <Typography variant="body2">
                      {value ? String(value) : 'Not found'}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1">
                Line Items ({previewResult.line_items?.length || 0})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {previewResult.line_items?.length > 0 ? (
                previewResult.line_items.map((item: any, index: number) => (
                  <Box key={index} sx={{ mb: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                    <Typography variant="body2"><strong>Description:</strong> {item.description}</Typography>
                    <Typography variant="body2"><strong>Quantity:</strong> {item.quantity}</Typography>
                    <Typography variant="body2"><strong>Unit Price:</strong> €{item.unit_price}</Typography>
                    <Typography variant="body2"><strong>Total:</strong> €{item.total_amount}</Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No line items found
                </Typography>
              )}
            </AccordionDetails>
          </Accordion>

          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1">Confidence Scores</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(previewResult.confidence_scores).map(([field, score]) => (
                  <Chip
                    key={field}
                    label={`${field}: ${Math.round((score as number) * 100)}%`}
                    color={score as number > 0.7 ? 'success' : score as number > 0.4 ? 'warning' : 'error'}
                    size="small"
                  />
                ))}
              </Box>
            </AccordionDetails>
          </Accordion>
        </Paper>
      )}

      {/* Conversion Result */}
      {conversionResult && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            <CheckCircle color="success" sx={{ mr: 1, verticalAlign: 'middle' }} />
            Conversion Result
          </Typography>

          <Alert 
            severity={
              conversionResult.status === 'completed' ? 'success' : 
              conversionResult.status === 'failed' ? 'error' :
              conversionResult.status === 'processing' ? 'info' : 'info'
            } 
            sx={{ mb: 2 }}
          >
            {conversionResult.message}
            {conversionResult.status === 'processing' && (
              <LinearProgress sx={{ mt: 1 }} />
            )}
          </Alert>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Job ID: {conversionResult.job_id}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                File: {conversionResult.pdf_filename}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Template: {conversionResult.template_used || 'Auto-detect'}
              </Typography>
            </Box>

            {(conversionResult.status === 'completed' || conversionResult.ubl_xml) && (
              <Button
                variant="contained"
                startIcon={<Download />}
                onClick={downloadUBL}
                sx={{ alignSelf: 'flex-start' }}
              >
                Download UBL XML
              </Button>
            )}

            {conversionResult.extraction_data && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle1">Extracted Data</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <pre style={{ fontSize: '0.8rem', overflow: 'auto' }}>
                    {JSON.stringify(conversionResult.extraction_data, null, 2)}
                  </pre>
                </AccordionDetails>
              </Accordion>
            )}
          </Box>
        </Paper>
      )}

      {/* Batch Conversion Results */}
      {batchResult && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            <Archive color="primary" sx={{ mr: 1, verticalAlign: 'middle' }} />
            Batch Conversion Results
          </Typography>

          <Alert severity="info" sx={{ mb: 2 }}>
            Batch ID: {batchResult.batch_id} - {batchResult.message}
          </Alert>

          {batchJobs.length > 0 && (
            <>
              <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
                <Typography variant="subtitle1">
                  Progress: {batchJobs.filter(job => job.status === 'completed').length} / {batchJobs.length} completed
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<Refresh />}
                  onClick={() => {
                    batchResult.job_ids.forEach(jobId => pollJobStatus(jobId, true));
                  }}
                >
                  Refresh Status
                </Button>
              </Box>

              <List>
                {batchJobs.map((job, index) => (
                  <ListItem key={job.job_id} sx={{ px: 0 }}>
                    <ListItemIcon>
                      <Badge
                        color={
                          job.status === 'completed' ? 'success' :
                          job.status === 'failed' ? 'error' :
                          job.status === 'processing' ? 'warning' : 'default'
                        }
                        variant="dot"
                      >
                        <PictureAsPdf />
                      </Badge>
                    </ListItemIcon>
                    <ListItemText
                      primary={job.pdf_filename}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            Status: {job.status}
                          </Typography>
                          {job.status === 'processing' && (
                            <LinearProgress sx={{ mt: 0.5, height: 3 }} />
                          )}
                        </Box>
                      }
                    />
                    {job.status === 'completed' && (
                      <Button
                        size="small"
                        startIcon={<Download />}
                        onClick={async () => {
                          try {
                            const blob = await apiService.downloadUblXml(job.job_id);
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${job.pdf_filename.replace('.pdf', '')}.xml`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                          } catch (error) {
                            enqueueSnackbar('Fout bij downloaden', { variant: 'error' });
                          }
                        }}
                      >
                        Download
                      </Button>
                    )}
                  </ListItem>
                ))}
              </List>

              {batchJobs.filter(job => job.status === 'completed').length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="contained"
                    startIcon={<Archive />}
                    onClick={downloadBatchZip}
                    color="success"
                  >
                    Download All as ZIP ({batchJobs.filter(job => job.status === 'completed').length} files)
                  </Button>
                </Box>
              )}
            </>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default ConversionPage;