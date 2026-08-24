import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const processEmergency = async (data) => {
  const response = await API.post("/process", data);
  return response.data;
};
