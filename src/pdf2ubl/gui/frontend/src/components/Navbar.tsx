import React from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box,
  IconButton,
  Menu,
  MenuItem
} from '@mui/material';
import { 
  Dashboard,
  Transform,
  Description,
  SmartToy,
  Settings,
  MoreVert
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    handleMenuClose();
  };

  const isActivePath = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const navigationItems = [
    { path: '/', label: 'Dashboard', icon: <Dashboard /> },
    { path: '/convert', label: 'Convert', icon: <Transform /> },
    { path: '/templates', label: 'Templates', icon: <Description /> },
    { path: '/ml', label: 'ML Features', icon: <SmartToy /> },
    { path: '/settings', label: 'Settings', icon: <Settings /> },
  ];

  return (
    <AppBar position="static" sx={{ mb: 0 }}>
      <Toolbar>
        <Typography 
          variant="h6" 
          component="div" 
          sx={{ flexGrow: 0, mr: 4, cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          📄 PDF2UBL
        </Typography>

        {/* Desktop Navigation */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, flexGrow: 1 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              sx={{
                mr: 2,
                backgroundColor: isActivePath(item.path) ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* Mobile Navigation */}
        <Box sx={{ display: { xs: 'flex', md: 'none' }, flexGrow: 1, justifyContent: 'flex-end' }}>
          <IconButton
            size="large"
            aria-label="navigation menu"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMenuOpen}
            color="inherit"
          >
            <MoreVert />
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            {navigationItems.map((item) => (
              <MenuItem 
                key={item.path}
                onClick={() => handleNavigate(item.path)}
                selected={isActivePath(item.path)}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 1 }}>
                  {item.icon}
                </Box>
                {item.label}
              </MenuItem>
            ))}
          </Menu>
        </Box>

        {/* Version info */}
        <Typography 
          variant="caption" 
          sx={{ 
            display: { xs: 'none', sm: 'block' },
            opacity: 0.7,
            ml: 2 
          }}
        >
          v1.0.0
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;