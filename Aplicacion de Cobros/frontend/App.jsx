import React, { useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet, Alert } from 'react-native';
import { registerForPushNotificationsAsync } from './notification';
import Constants from 'expo-constants';
export default function App() {
  const [token, setToken] = useState('');
  const API_URL = Constants.expoConfig?.extra?.apiUrl || process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
  useEffect(() => {
    registerForPushNotificationsAsync().then(t => setToken(t));
  }, []);
  const handleRegister = async () => {
    if (!token) return Alert.alert('Error', 'No token available');
    try {
      const res = await fetch(`${API_URL}/notifications/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, user_id: 1 }),
      });
      const data = await res.json();
      Alert.alert('Success', JSON.stringify(data));
    } catch (e) {
      Alert.alert('Error', e.message);
    }
  };
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Apicobros</Text>
      <Text style={styles.token}>Token: {token || 'Loading...'}</Text>
      <Button title="Register Token" onPress={handleRegister} />
    </View>
  );
}
const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  token: { fontSize: 12, marginBottom: 20, textAlign: 'center' },
});