import React from 'react';
import { Cpu, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '../common/Button';
import './TicketStatus.css';

export const TicketStatus = ({ ticketStatusData, onRetry }) => {
  const isReady = ticketStatusData?.status === 'READY';
  const isFailed = ticketStatusData?.status === 'FAILED';

  return (
    <div className="ev-ticket-status-box">
      <div className="ev-status-banner-header">
        <Cpu size={20} className="ev-rabbitmq-icon" />
        <span className="ev-worker-tag">ASYNC TICKET GENERATION ENGINE (RABBITMQ + WORKER)</span>
      </div>

      <div className="ev-status-body">
        {isReady ? (
          <div className="ev-status-state ev-status-state--ready">
            <CheckCircle2 size={36} className="ev-state-icon ready" />
            <div>
              <h4>Ticket Issued & Signed Successfully</h4>
              <p>Your cryptographically signed QR ticket is ready in your account.</p>
            </div>
          </div>
        ) : isFailed ? (
          <div className="ev-status-state ev-status-state--failed">
            <AlertCircle size={36} className="ev-state-icon failed" />
            <div>
              <h4>Ticket Generation Encountered Delay</h4>
              <p>The worker node is retrying execution.</p>
              {onRetry && (
                <Button variant="secondary" size="sm" onClick={onRetry} className="ev-retry-btn">
                  Retry Status Check
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="ev-status-state ev-status-state--processing">
            <Loader2 size={36} className="ev-state-icon processing" />
            <div>
              <h4>Your ticket is being generated.</h4>
              <p className="ev-step-msg">{ticketStatusData?.stepMessage || "Processing async queue task..."}</p>
              <div className="ev-progress-bar-mini">
                <div 
                  className="ev-progress-fill" 
                  style={{ width: `${ticketStatusData?.progress || 35}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
