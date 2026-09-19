import { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Typography, List, ListItem, ListItemText, CircularProgress, Alert } from '@mui/material';

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFavorites = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/favorites`);
        setFavorites(response.data);
      } catch (err) {
        setError('Failed to fetch favorite words.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchFavorites();
  }, []);

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 4 }}>
        Favorite Words
      </Typography>
      {loading ? (
        <CircularProgress />
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <List>
          {favorites.length > 0 ? (
            favorites.map((word, index) => (
              <ListItem key={index}>
                <ListItemText primary={word} />
              </ListItem>
            ))
          ) : (
            <Typography>No favorite words yet.</Typography>
          )}
        </List>
      )}
    </Container>
  );
}

export default App;
