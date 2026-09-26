// Placeholder for actual API client
export const restoreImage = async (file, options) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(file);
    }, 4500);
  });
};

export const identifyMonument = async (file) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ id: 'taj-mahal' });
    }, 4500);
  });
};

export const getMonumentHistory = async (id) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id,
        name: 'Taj Mahal',
        location: 'Agra, Uttar Pradesh, India',
        built_year: '1631–1653',
        description: 'The Taj Mahal is an ivory-white marble mausoleum on the right bank of the river Yamuna in Agra, Uttar Pradesh, India. It was commissioned in 1631 by the fifth Mughal emperor, Shah Jahan to house the tomb of his beloved wife, Mumtaz Mahal; it also houses the tomb of Shah Jahan himself.',
        image_url: 'https://images.unsplash.com/photo-1564507592208-528756d11f62?q=80&w=2000&auto=format&fit=crop',
        source_url: 'https://en.wikipedia.org/wiki/Taj_Mahal',
        timeline: [
          {
            year: '1631',
            title: 'Commissioned by Shah Jahan',
            description: 'Construction of the mausoleum essentially began, overseen by a board of architects.'
          },
          {
            year: '1643',
            title: 'Main Mausoleum Completed',
            description: 'The primary structure and the dome were completed, while work continued on the surrounding buildings and garden.'
          },
          {
            year: '1653',
            title: 'Complex Fully Completed',
            description: 'The entire complex was completed at an estimated cost of 32 million rupees, which in 2020 would be approximately 70 billion rupees (about U.S. $1 billion).'
          },
          {
            year: '1983',
            title: 'UNESCO World Heritage Site',
            description: 'Designated as a UNESCO World Heritage Site for being "the jewel of Muslim art in India and one of the universally admired masterpieces of the world\'s heritage".'
          }
        ]
      });
    }, 1500);
  });
};
