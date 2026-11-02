export interface ModelOption {
  id: string;
  label: string;
  recommended?: boolean;
}

export interface ProviderConfig {
  name: string;
  env_key: string;
  key_placeholder: string;
  default_model: string;
  models: ModelOption[];
}

export interface ShortlistItem {
  rank: number;
  name: string;
  symbol: string;
  ch24h: number;
  ch7d: number;
  compression_ratio: number;
  vmc_ratio: number;
  price: string;
}

export interface TradeCard {
  coin: string;
  direction: string;
  platform: string;
  setup_structure?: string;
  technical_reason?: string;
  target_zone?: string;
}

export interface StreamEvent {
  type: 'status' | 'shortlist' | 'agent_step' | 'done' | 'error';
  stage?: string;
  message?: string;
  data?: ShortlistItem[];
  step?: number;
  goal?: string;
  action?: string;
  memory?: string;
  cards?: TradeCard[];
  raw_output?: string;
}
