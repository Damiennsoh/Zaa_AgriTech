import { Metadata } from "next";
import BuyerDashboardClient from "./BuyerDashboardClient";

export const metadata: Metadata = {
  title: "ZAA Buyer Dashboard",
  description: "Browse AI-graded agricultural produce from Northern Ghana",
};

export default function BuyerDashboard() {
  return <BuyerDashboardClient />;
}
