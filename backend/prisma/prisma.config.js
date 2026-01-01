import { defineConfig } from "@prisma/config";

export default defineConfig({
  database: {
    url: process.env.DATABASE_URL,   // moved here
  },
});
