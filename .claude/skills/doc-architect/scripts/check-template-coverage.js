#!/usr/bin/env node
/**
 * check-template-coverage.js
 * Analyzes how well Structured Notes content maps to generated final documents.
 * Identifies content that may be missing from final outputs.
 */

const fs = require('fs');
const path = require('path');

// ANSI colors
const Colors = {
  RED: '\033[0;31m',
  GREEN: '\033[0;32m',
  YELLOW: '\033[1;33m',
  BLUE: '\033[0;34m',
  NC: '\033[0m'
};

/**
 * Print formatted header
 */
function printHeader(title) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`  ${title}`);
  console.log('='.repeat(60));
}

/**
 * Extract key points from 00_Key_Points_List.md
 */
function extractKeyPoints(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const sections = {};
  let currentSection = null;

  const lines = content.split('\n');
  for (const line of lines) {
    if (line.startsWith('## ')) {
      currentSection = line.substring(3).trim();
      sections[currentSection] = [];
    } else if (line.startsWith('- ') && currentSection) {
      sections[currentSection].push(line.substring(2).trim());
    }
  }

  return sections;
}

/**
 * Extract structured notes from 01_Structured_Notes.md
 */
function extractStructuredNotes(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }

  const content = fs.readFileSync(filePath, 'utf8');
  const notes = {};
  let currentDimension = null;
  let currentSubsection = null;

  const lines = content.split('\n');
  for (const line of lines) {
    // Match [Dimension X] Name
    const dimMatch = line.match(/\[Dimension.*?\]\s*(.+)/);
    if (dimMatch) {
      currentDimension = dimMatch[1];
      notes[currentDimension] = {};
      continue;
    }

    // Match subsection headers
    if (line.startsWith('### ')) {
      currentSubsection = line.substring(4).trim();
      if (currentDimension) {
        notes[currentDimension][currentSubsection] = [];
      }
      continue;
    }

    // Match list items
    if (line.startsWith('- ') || line.startsWith('[')) {
      const item = line.replace(/^- /, '').replace(/\[|\]/g, '').trim();
      if (currentDimension && currentSubsection) {
        notes[currentDimension][currentSubsection].push(item);
      }
    }
  }

  return notes;
}

/**
 * Extract content from all final documents
 */
function extractDocumentContent(docsDir) {
  const finalDocs = {};
  const finalPatterns = [
    '02_PRD.md',
    '03_System_Architecture.md',
    '04_API_Documentation.md',
    '01_Problem_Definition.md',
    '02_Solution_Design.md',
    '03_Action_Plan.md'
  ];

  for (const pattern of finalPatterns) {
    const filePath = path.join(docsDir, pattern);
    if (fs.existsSync(filePath)) {
      finalDocs[pattern] = fs.readFileSync(filePath, 'utf8').toLowerCase();
    }
  }

  return finalDocs;
}

/**
 * Check which items from structured notes are covered in final documents
 */
function checkCoverage(structuredNotes, finalDocs) {
  const covered = [];
  const notCovered = [];

  for (const [dimension, subsections] of Object.entries(structuredNotes)) {
    for (const [subsection, items] of Object.entries(subsections)) {
      for (const item of items) {
        // Extract key terms from item (first 30 chars)
        const keyTerms = item.substring(0, 30).toLowerCase();

        let found = false;
        for (const [docName, docContent] of Object.entries(finalDocs)) {
          if (docContent.includes(keyTerms)) {
            covered.push({
              item,
              dimension,
              subsection,
              foundIn: docName
            });
            found = true;
            break;
          }
        }

        if (!found) {
          notCovered.push({
            item,
            dimension,
            subsection
          });
        }
      }
    }
  }

  return { covered, notCovered };
}

/**
 * Analyze 99_Value_Details.md for coverage statistics
 */
function analyzeValueDetails(docsDir) {
  const valueFile = path.join(docsDir, '99_Value_Details.md');
  if (!fs.existsSync(valueFile)) {
    return {};
  }

  const content = fs.readFileSync(valueFile, 'utf8');
  const categories = [
    'Future Considerations',
    'Alternative Approaches',
    'Implementation Details',
    'User Insights',
    'Edge Cases',
    'Dependencies',
    'Open Questions'
  ];

  const stats = {};
  for (const category of categories) {
    const pattern = `## ${category}`;
    if (content.includes(pattern)) {
      const sectionIndex = content.indexOf(pattern);
      const section = content.substring(sectionIndex);
      // Count table rows (lines starting with |)
      const rows = section.split('\n').filter(l => l.startsWith('|') && !l.startsWith('|---')).length;
      stats[category] = Math.max(0, rows - 1); // Subtract header row
    }
  }

  return stats;
}

/**
 * Main function
 */
function main() {
  const docsDir = process.argv[2] || './doc-arch';

  if (!fs.existsSync(docsDir)) {
    console.log(`${Colors.RED}Error: Directory '${docsDir}' does not exist${Colors.NC}`);
    process.exit(1);
  }

  printHeader('DOC-ARCHITECT TEMPLATE COVERAGE ANALYZER');
  console.log(`\nAnalyzing directory: ${docsDir}`);

  // Extract content
  const keyPoints = extractKeyPoints(path.join(docsDir, '00_Key_Points_List.md'));
  const structuredNotes = extractStructuredNotes(path.join(docsDir, '01_Structured_Notes.md'));
  const finalDocs = extractDocumentContent(docsDir);
  const valueStats = analyzeValueDetails(docsDir);

  // Check coverage
  const { covered, notCovered } = checkCoverage(structuredNotes, finalDocs);

  const totalItems = covered.length + notCovered.length;
  const coverageRate = totalItems > 0 ? (covered.length / totalItems * 100) : 0;

  // Print results
  printHeader('COVERAGE SUMMARY');
  console.log(`Total Items Analyzed:  ${totalItems}`);
  console.log(`Covered in Docs:      ${covered.length}`);
  console.log(`Not Covered:           ${notCovered.length}`);
  console.log(`Coverage Rate:        ${coverageRate.toFixed(1)}%`);

  // Coverage quality assessment
  if (coverageRate >= 90) {
    console.log(`\n${Colors.GREEN}✓ Excellent coverage!${Colors.NC}`);
  } else if (coverageRate >= 80) {
    console.log(`\n${Colors.YELLOW}⚠ Good coverage, room for improvement${Colors.NC}`);
  } else {
    console.log(`\n${Colors.RED}✗ Low coverage - review recommended${Colors.NC}`);
  }

  // Value details summary
  if (Object.keys(valueStats).length > 0) {
    printHeader('VALUE DETAILS CAPTURE');
    const totalValueItems = Object.values(valueStats).reduce((sum, val) => sum + val, 0);
    console.log(`Total Value Items: ${totalValueItems}`);
    for (const [category, count] of Object.entries(valueStats)) {
      console.log(`  ${category}: ${count}`);
    }
  }

  // Not covered items
  if (notCovered.length > 0) {
    printHeader('NOT COVERED ITEMS');
    console.log(`\nThe following ${notCovered.length} items may need attention:\n`);

    const displayItems = notCovered.slice(0, 20); // Limit to first 20
    for (const item of displayItems) {
      console.log(`${Colors.YELLOW}•${Colors.NC} ${item.item.substring(0, 60)}...`);
      console.log(`  From: ${item.dimension} > ${item.subsection}`);
    }

    if (notCovered.length > 20) {
      console.log(`\n... and ${notCovered.length - 20} more items`);
    }

    console.log(`\n${Colors.BLUE}Note: These items may be captured in 99_Value_Details.md${Colors.NC}`);
  }

  // Recommendations
  printHeader('RECOMMENDATIONS');

  if (coverageRate < 80) {
    console.log(`\n${Colors.YELLOW}• Coverage is below 80% - consider expanding final documents${Colors.NC}`);
    console.log(`• Review not_covered items and determine if they should be in final docs`);
    console.log(`• Ensure 99_Value_Details.md captures valuable items not in templates`);
  }

  if (Object.keys(valueStats).length === 0) {
    console.log(`\n${Colors.RED}• 99_Value_Details.md not found - value details may be lost${Colors.NC}`);
  } else {
    const totalValueItems = Object.values(valueStats).reduce((sum, val) => sum + val, 0);
    if (totalValueItems < notCovered.length) {
      console.log(`\n${Colors.YELLOW}• Some not_covered items may not be in 99_Value_Details.md${Colors.NC}`);
    }
  }

  if (Object.keys(finalDocs).length === 0) {
    console.log(`\n${Colors.RED}• No final documents found - run document generation first${Colors.NC}`);
  }

  console.log('\n' + '='.repeat(60));

  // Exit with appropriate code
  process.exit(coverageRate >= 80 ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main();
}
