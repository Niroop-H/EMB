/*
 * MAH Quantum - Autonomous Hardware Copilot Panel.
 * Devashri S Embedded System Technologies.
 * Powered by KiCad EDA Core (https://www.kicad.org).
 *
 * Copyright (C) 2026 Devashri S Embedded System Technologies & MAH Quantum.
 * All Rights Reserved. Proprietary and Confidential.
 */

#ifndef AI_COPILOT_PANE_H
#define AI_COPILOT_PANE_H

#include <wx/panel.h>
#include <wx/sizer.h>
#include <wx/textctrl.h>
#include <wx/button.h>
#include <wx/stattext.h>
#include <wx/gauge.h>
#include <wx/string.h>

class KICAD_MANAGER_FRAME;

class AI_COPILOT_PANE : public wxPanel
{
public:
    AI_COPILOT_PANE( wxWindow* aParent );
    virtual ~AI_COPILOT_PANE();

    void AppendLog( const wxString& aMessage );
    void SetPipelineProgress( int aPercent, const wxString& aStageName );
    void TriggerHardwareSynthesis( const wxString& aPrompt );

private:
    void OnGenerateClicked( wxCommandEvent& aEvent );
    void OnSolveErcDrcClicked( wxCommandEvent& aEvent );
    void OnExportTapeoutClicked( wxCommandEvent& aEvent );

    wxTextCtrl*     m_promptInput;
    wxButton*       m_btnGenerate;
    wxButton*       m_btnSolveDrc;
    wxButton*       m_btnTapeout;
    wxStaticText*   m_statusLabel;
    wxGauge*        m_progressBar;
    wxTextCtrl*     m_logOutput;

    wxDECLARE_EVENT_TABLE();
};

#endif // AI_COPILOT_PANE_H
