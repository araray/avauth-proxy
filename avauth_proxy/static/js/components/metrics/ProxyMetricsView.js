import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TabsContent, Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Activity,
  AlertTriangle,
  ArrowUpDown,
  CheckCircle,
} from "lucide-react";
import _ from "lodash";

const ProxyMetricsView = ({ proxyId }) => {
  const [metrics, setMetrics] = useState(null);
  const [timeframe, setTimeframe] = useState("1h");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch metrics data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `/metrics/proxy/${proxyId}/data?timeframe=${timeframe}`,
        );
        if (!response.ok) throw new Error("Failed to fetch metrics");
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [proxyId, timeframe]);

  if (loading) return <div className="p-4">Loading metrics...</div>;
  if (error)
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  if (!metrics) return null;

  const healthScore = metrics.health?.score || 0;
  const healthColor =
    healthScore > 80
      ? "text-green-500"
      : healthScore > 60
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="space-y-6">
      {/* Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Health Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-background rounded-lg">
              <div className={`text-4xl font-bold ${healthColor}`}>
                {healthScore}%
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                Health Score
              </div>
            </div>
            <div className="text-center p-4 bg-background rounded-lg">
              <div className="text-4xl font-bold text-blue-500">
                {metrics.summary?.uptime || "100"}%
              </div>
              <div className="text-sm text-muted-foreground mt-1">Uptime</div>
            </div>
            <div className="text-center p-4 bg-background rounded-lg">
              <div className="text-4xl font-bold text-purple-500">
                {metrics.summary?.response_time || "0"}ms
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                Avg Response Time
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Charts */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Performance Metrics</CardTitle>
            <Select value={timeframe} onValueChange={setTimeframe}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Timeframe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">24 Hours</SelectItem>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="30d">30 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="requests">
            <TabsList>
              <TabsTrigger value="requests">Requests</TabsTrigger>
              <TabsTrigger value="latency">Latency</TabsTrigger>
              <TabsTrigger value="errors">Errors</TabsTrigger>
              <TabsTrigger value="bandwidth">Bandwidth</TabsTrigger>
            </TabsList>

            <TabsContent value="requests" className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.requests}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#2563eb" />
                </LineChart>
              </ResponsiveContainer>
            </TabsContent>

            <TabsContent value="latency" className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.latency}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#7c3aed" />
                </LineChart>
              </ResponsiveContainer>
            </TabsContent>

            <TabsContent value="errors" className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.errors}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#dc2626" />
                </LineChart>
              </ResponsiveContainer>
            </TabsContent>

            <TabsContent value="bandwidth" className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.bandwidth}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="incoming"
                    stroke="#2563eb"
                    name="Incoming"
                  />
                  <Line
                    type="monotone"
                    dataKey="outgoing"
                    stroke="#16a34a"
                    name="Outgoing"
                  />
                </LineChart>
              </ResponsiveContainer>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Alerts & Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {metrics.insights?.map((insight, index) => (
              <Alert key={index} variant={insight.type}>
                {insight.type === "success" ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertTriangle className="h-4 w-4" />
                )}
                <AlertDescription>{insight.message}</AlertDescription>
              </Alert>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProxyMetricsView;
