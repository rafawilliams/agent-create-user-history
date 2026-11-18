import {
  AppBar,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useState } from 'react';
import { MenuIcon } from './icons';

interface AppHeaderProps {
  showLogout: boolean;
  onLogout: () => void;
}

/** Encabezado con el nombre del agente y "Cerrar sesion" (en móvil, dentro de un menú; BR5.8). */
export default function AppHeader({ showLogout, onLogout }: AppHeaderProps) {
  const theme = useTheme();
  const compact = useMediaQuery(theme.breakpoints.down('sm'), { noSsr: true });
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);

  return (
    <AppBar position="static" enableColorOnDark>
      <Toolbar>
        <Typography variant="h6" component="h1" sx={{ flexGrow: 1 }}>
          Agente analista de negocio
        </Typography>
        {showLogout && !compact && (
          <Button color="inherit" onClick={onLogout}>
            Cerrar sesion
          </Button>
        )}
        {showLogout && compact && (
          <>
            <IconButton
              color="inherit"
              aria-label="Abrir menú"
              aria-haspopup="menu"
              aria-expanded={anchor !== null}
              onClick={(event) => setAnchor(event.currentTarget)}
            >
              <MenuIcon />
            </IconButton>
            <Menu anchorEl={anchor} open={anchor !== null} onClose={() => setAnchor(null)}>
              <MenuItem
                onClick={() => {
                  setAnchor(null);
                  onLogout();
                }}
              >
                Cerrar sesion
              </MenuItem>
            </Menu>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
}
