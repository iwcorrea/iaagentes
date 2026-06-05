import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
export default function DashboardCliente() {
  const [payments, setPayments] = useState([]);
  const [total, setTotal] = useState(0);
  useEffect(() => {
    const fetchMyPayments = async () => {
      const res = await apiClient.get('/payments/my-payments');
      setPayments(res.data);
      setTotal(res.data.reduce((acc, curr) => acc + curr.amount, 0));
    };
    fetchMyPayments();
  }, []);
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">My Payments</h1>
      <div className="bg-blue-100 p-6 rounded-lg mb-6 text-2xl font-semibold">
        Total Paid: ${total}
      </div>
      <div className="bg-white rounded shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-200"><tr><th>Date</th><th>Amount</th><th>Note</th></tr></thead>
          <tbody>
            {payments.map(p => (
              <tr key={p.id} className="border-t"><td>{new Date(p.date).toLocaleDateString()}</td><td>${p.amount}</td><td>{p.description}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}